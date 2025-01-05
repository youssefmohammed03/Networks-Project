import socket
import struct
import threading
import json
import ssl
import frame_processor as fm
from Database import *
import frames
import HPACK as hpack
import error_handling as error
from logger_setup import get_logger
import tkinter as tk
from tkinter import ttk, scrolledtext
import logging

logger = get_logger()

HTTP2_PREFACE = b"PRI * HTTP/2.0\r\n\r\nSM\r\n\r\n"
SETTINGS_FRAME_TYPE = 0x4
SETTINGS_ACK_FLAG = 0x1

def read_exact(sock, length):
    data = b""
    while len(data) < length:
        chunk = sock.recv(length - len(data))
        if not chunk:
            raise ConnectionError("Connection closed by client.")
        data += chunk
    return data

def decode_settings_frame(payload):
    i = 0
    settings = {}
    while i < len(payload):
        setting_id, value = struct.unpack("!H I", payload[i:i + 6])
        i += 6

        setting_names = {
            0x01: "SETTINGS_HEADER_TABLE_SIZE",
            0x02: "SETTINGS_ENABLE_PUSH",
            0x03: "SETTINGS_MAX_CONCURRENT_STREAMS",
            0x04: "SETTINGS_INITIAL_WINDOW_SIZE",
            0x05: "SETTINGS_MAX_FRAME_SIZE",
        }
        
        setting_name = setting_names.get(setting_id, "Unknown")
        settings[setting_name] = value

        logger.info(f"Setting Identifier: {setting_id} ({setting_name}) = {value}")

    return settings

def send_settings_frame(client_socket, file_path="server_settings.json"):
    try:
        with open(file_path, "r") as file:
            server_settings = json.load(file)
    except FileNotFoundError:
        logger.info("Settings file not found.")
        return

    identifier_map = {
        "SETTINGS_HEADER_TABLE_SIZE": 0x1,
        "SETTINGS_ENABLE_PUSH": 0x2,
        "SETTINGS_MAX_CONCURRENT_STREAMS": 0x3,
        "SETTINGS_INITIAL_WINDOW_SIZE": 0x4,
        "SETTINGS_MAX_FRAME_SIZE": 0x5
    }

    payload = b""
    for key, value in server_settings.items():
        if key in identifier_map:
            payload += struct.pack("!H I", identifier_map[key], value)

    settings_frame = (struct.pack("!I", len(payload))[1:] + struct.pack("!B", 0x4) + struct.pack("!B", 0) + struct.pack("!I", 0) + payload)

    client_socket.sendall(settings_frame)
    logger.info("SETTINGS FRAME sent to client.")

def send_server_ack_settings_frame(client_socket):
    ack_settings_frame = (struct.pack("!I", 0)[1:] + struct.pack("!B", SETTINGS_FRAME_TYPE) + struct.pack("!B", SETTINGS_ACK_FLAG) + struct.pack("!I", 0))
    client_socket.sendall(ack_settings_frame)
    logger.info("ACK SETTINGS FRAME sent to client.")

def store_client_settings(frame_length, settings_payload, client_address):
    for i in range(0, frame_length, 6):
        key, value = struct.unpack("!H I", settings_payload[i:i + 6])
        client_settings[client_address][key] = value 
    sizes_for_sockets[client_address] = 65535
    sizes_for_sockets_for_clients[client_address] = client_settings[client_address][0x4]
    logger.info(f"Stored settings for client.")

def settings_frame_handler(client_socket, client_address, frame):
    if frame.get_stream_id() != 0:
        logger.info("Invalid stream ID in settings frame. Closing connection.")
        return
    
    if frame.get_frame_flags() == SETTINGS_ACK_FLAG:
        logger.info("ACK SETTINGS FRAME received from client.")
        return

    decode_settings_frame(frame.get_payload())
    
    store_client_settings(frame.get_frame_length(), frame.get_payload(), client_address)

    logger.info("Settings Frame received from client and stored.")

    send_settings_frame(client_socket)
    
    send_server_ack_settings_frame(client_socket)

def print_bytes_in_binary(byte_data):
    binary_strings = [bin(byte)[2:].zfill(8) for byte in byte_data]
    logger.info(" ".join(binary_strings))

def handle_client_connection(client_socket, client_address):
    try:
        client_settings[client_address] = {}

        preface = read_exact(client_socket, len(HTTP2_PREFACE))
        if preface != HTTP2_PREFACE:
            logger.info("Invalid HTTP/2 preface received. Closing connection.")
            error.handle_connection_error(0, error.HTTP2ErrorCodes.PROTOCOL_ERROR, client_socket, reason="No valid HTTP/2 preface received.")
            return
        logger.info("PREFACE received from the client.")

        frame = frames.Frame(read_exact(client_socket, 9))  
        if (frame.get_frame_type() == SETTINGS_FRAME_TYPE):
            frame.set_payload(read_exact(client_socket, frame.get_frame_length()))
            settings_frame_handler(client_socket, client_address, frame)

        logger.info("Handing over to Frame Processor")
        fm.frame_processor(client_socket, client_address)

    except Exception as e:
        logger.info(f"Error: {e}")
        error.handle_connection_error(0, error.HTTP2ErrorCodes.PROTOCOL_ERROR, client_socket, reason="")
    finally:
        if client_address in client_settings:
            del client_settings[client_address]
        if client_address in client_dynamic_table:
            del client_dynamic_table[client_address]
        if client_address in sizes_for_sockets:
            del sizes_for_sockets[client_address]
        if client_address in sizes_for_sockets_for_clients:
            del sizes_for_sockets_for_clients[client_address]
        streams.clear()
        logger.info(f"Connection with {client_address} closed and its data deleted.")

def handle_client_thread(client_socket, client_address):
    handle_client_connection(client_socket, client_address)

def start_server(host="192.168.1.4", port=443):
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_socket.bind((host, port))
    server_socket.listen(10)
    logger.info(f"Server is listening on {host}:{port}")

    try:
        context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
        context.check_hostname = False
        context.verify_mode = ssl.CERT_NONE
        context.load_cert_chain(certfile='certificate.crt', keyfile='private.key')
        context.set_alpn_protocols(["h2", "http/1.1"])
    except ssl.SSLError as e:
        logger.info(f"SSL error: {e}")
        return
    try:
        while True:
            try:
                client_socket, client_address = server_socket.accept()
                secure_socket = context.wrap_socket(client_socket, server_side=True)
                selected_protocol = secure_socket.selected_alpn_protocol()
                if selected_protocol == "h2":
                    logger.info(f"HTTP/2")
                else:
                    logger.info(f"HTTP/1.1")
                client_address = client_address[0]
                sizes_for_sockets[client_address] = 0
                sizes_for_sockets_for_clients[client_address] = 0
                logger.info(f"Accepted connection from {client_address}")
                client_dynamic_table[client_address] = hpack.DynamicTable()
                client_thread = threading.Thread(target=handle_client_thread, args=(secure_socket, client_address))
                client_thread.start()
            except Exception as e:
                pass
    except KeyboardInterrupt:
        logger.info("Shutting down server...")
    finally:
        error.handle_connection_error(0, error.HTTP2ErrorCodes.NO_ERROR , secure_socket, reason="Shutting down server.")












def start_gui():
    root = tk.Tk()
    
    # Set the initial size of the window (width x height)
    initial_width = 800
    initial_height = 600
    root.geometry(f"{initial_width}x{initial_height}")
    
    # Allow the window to be resizable
    root.resizable(True, True)
    
    # Create the application
    app = ServerApp(root)
    
    # Start the main loop
    root.mainloop()

class ServerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Server Control Panel")

        # Create a container for pages
        self.container = tk.Frame(self.root)
        self.container.pack(fill="both", expand=True)  # Make the container expand

        # Configure the container grid to expand
        self.container.grid_rowconfigure(0, weight=1)  # Make row 0 expand
        self.container.grid_columnconfigure(0, weight=1)  # Make column 0 expand

        # Dictionary to hold pages
        self.pages = {}

        # Initialize pages
        self.create_login_page()
        self.create_control_page()
        self.create_log_page()

        # Show the login page initially
        self.show_page("Login")

        # Logger setup
        self.logger = get_logger()
        self.log_handler = TextHandler(self.pages["Log"].log_text)
        self.logger.addHandler(self.log_handler)

    def create_login_page(self):
        frame = LoginPage(self.container, self.show_page)
        self.pages["Login"] = frame
        frame.grid(row=0, column=0, sticky="nsew")  # Make the frame expand and fill space

    def create_control_page(self):
        frame = ControlPage(self.container, self.show_page, self.start_server)
        self.pages["Control"] = frame
        frame.grid(row=0, column=0, sticky="nsew")  # Make the frame expand and fill space

    def create_log_page(self):
        frame = LogPage(self.container, self.show_page)
        self.pages["Log"] = frame
        frame.grid(row=0, column=0, sticky="nsew")  # Make the frame expand and fill space

    def show_page(self, page_name):
        page = self.pages[page_name]
        page.tkraise()

    def start_server(self):
        server_thread = threading.Thread(target=start_server, daemon=True)
        server_thread.start()
        self.logger.info("Server started.")

class LoginPage(tk.Frame):
    def __init__(self, parent, show_page):
        super().__init__(parent)
        self.show_page = show_page

        # Configure the frame to expand
        self.grid_rowconfigure(0, weight=1)  # Make row 0 expand
        self.grid_columnconfigure(0, weight=1)  # Make column 0 expand

        # Create a sub-frame to center the content
        center_frame = tk.Frame(self)
        center_frame.grid(row=0, column=0)

        tk.Label(center_frame, text="Username:").pack(pady=5)
        self.username_entry = tk.Entry(center_frame)
        self.username_entry.pack(pady=5)

        tk.Label(center_frame, text="Password:").pack(pady=5)
        self.password_entry = tk.Entry(center_frame, show="*")
        self.password_entry.pack(pady=5)

        self.error_label = tk.Label(center_frame, text="", fg="red")
        self.error_label.pack()

        tk.Button(center_frame, text="Login", command=self.validate_login).pack(pady=10)

    def validate_login(self):
        username = self.username_entry.get()
        password = self.password_entry.get()

        if username == "admin" and password == "admin":
            self.show_page("Control")
        else:
            self.error_label.config(text="Invalid username or password")

class ControlPage(tk.Frame):
    def __init__(self, parent, show_page, start_server_callback):
        super().__init__(parent)
        self.show_page = show_page
        self.start_server_callback = start_server_callback

        # Configure the frame to expand
        self.grid_rowconfigure(0, weight=1)  # Make row 0 expand
        self.grid_columnconfigure(0, weight=1)  # Make column 0 expand

        # Create a sub-frame to center the content
        center_frame = tk.Frame(self)
        center_frame.grid(row=0, column=0)

        tk.Label(center_frame, text="Server Control Panel", font=("Arial", 16)).pack(pady=10)

        tk.Button(center_frame, text="View Logs", command=lambda: self.show_page("Log")).pack(pady=10)
        tk.Button(center_frame, text="Start Server", command=self.start_server).pack(pady=10)

    def start_server(self):
        self.start_server_callback()

class LogPage(tk.Frame):
    def __init__(self, parent, show_page):
        super().__init__(parent)
        self.show_page = show_page

        # Configure the frame to expand
        self.grid_rowconfigure(0, weight=1)  # Make row 0 expand
        self.grid_columnconfigure(0, weight=1)  # Make column 0 expand

        # Create a sub-frame to center the content
        center_frame = tk.Frame(self)
        center_frame.grid(row=0, column=0, sticky="nsew")

        tk.Label(center_frame, text="Server Logs", font=("Arial", 16)).pack(pady=10)

        self.log_text = scrolledtext.ScrolledText(center_frame, state="disabled", height=15)
        self.log_text.pack(fill="both", expand=True, pady=10, padx=10)  # Make it expand and fill space

        tk.Button(center_frame, text="Back", command=lambda: self.show_page("Control")).pack(pady=10)

class TextHandler(logging.Handler):
    def __init__(self, text_widget):
        super().__init__()
        self.text_widget = text_widget

    def emit(self, record):
        msg = self.format(record)
        self.text_widget.configure(state="normal")
        self.text_widget.insert("end", msg + "\n")
        self.text_widget.configure(state="disabled")
        self.text_widget.see("end")

if __name__ == "__main__":
    start_gui()