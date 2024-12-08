import socket
import struct
import threading
import json

HTTP2_PREFACE = b"PRI * HTTP/2.0\r\n\r\nSM\r\n\r\n"
SETTINGS_FRAME_TYPE = 0x4
SETTINGS_ACK_FLAG = 0x1

client_settings = {}

def read_exact(sock, length):
    data = b""
    while len(data) < length:
        chunk = sock.recv(length - len(data))
        if not chunk:
            raise ConnectionError("Connection closed by client.")
        data += chunk
    return data

def send_settings_frame(client_socket, file_path="server_settings.json"):
    try:
        with open(file_path, "r") as file:
            server_settings = json.load(file)
    except FileNotFoundError:
        print("Settings file not found.")
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
    print("Sent settings frame:", server_settings)

def send_server_ack_settings_frame(client_socket):
    ack_settings_frame = (struct.pack("!I", 0)[1:] + struct.pack("!B", SETTINGS_FRAME_TYPE) + struct.pack("!B", SETTINGS_ACK_FLAG) + struct.pack("!I", 0))
    client_socket.sendall(ack_settings_frame)
    print("ACK settings frame sent to client.")

def store_client_settings(frame_length, settings_payload, client_address):
    for i in range(0, frame_length, 6):
        key, value = struct.unpack("!H I", settings_payload[i:i + 6])
        client_settings[client_address][key] = value 
    print(f"Stored settings for client {client_address}: {client_settings[client_address]}")

def client_ack_settings_frame(client_socket):
    ack_frame_header = read_exact(client_socket, 9)
    ack_frame_length, ack_frame_type, ack_frame_flags, ack_stream_id = struct.unpack("!I B B I", b"\x00" + ack_frame_header)
        
    if ack_frame_type != SETTINGS_FRAME_TYPE or ack_frame_flags != SETTINGS_ACK_FLAG or ack_stream_id != 0:
        print("Invalid ACK SETTINGS frame received. Closing connection.")
        client_socket.close()
        return

    print("ACK SETTINGS frame received from client. Connection setup complete.")

def settings_frame_handler(client_socket, client_address):
    frame_header = read_exact(client_socket, 9)
    frame_length, frame_type, frame_flags, stream_id = struct.unpack("!I B B I", b"\x00" + frame_header)
        
    if frame_type != SETTINGS_FRAME_TYPE:
        print("Invalid frame type received instead of settings. Closing connection.")
        client_socket.close()
        return
        
    if stream_id != 0:
        print("Invalid stream ID in settings frame. Closing connection.")
        client_socket.close()
        return

    settings_payload = read_exact(client_socket, frame_length)
    if frame_length % 6 != 0:
        print("Malformed settings frame payload. Closing connection.")
        client_socket.close()
        return
    print("Initial settings frame received from client:", settings_payload)
    
    store_client_settings(frame_length, settings_payload, client_address)

    send_server_ack_settings_frame(client_socket)

    send_settings_frame(client_socket)

    client_ack_settings_frame(client_socket)

def handle_client_connection(client_socket, client_address):
    try:
        client_settings[client_address] = {}

        preface = read_exact(client_socket, len(HTTP2_PREFACE))
        if preface != HTTP2_PREFACE:
            initial_data = (preface + client_socket.recv(1024)).decode()
            if "Upgrade: h2c" in initial_data or "Connection: Upgrade" in initial_data or "HTTP/1.1" in initial_data:
                response = (
                    "HTTP/1.1 101 Switching Protocols\r\n"
                    "Connection: Upgrade\r\n"
                    "Upgrade: h2c\r\n"
                    "\r\n"
                )
                client_socket.sendall(response.encode())
                print("HTTP/1.1 upgrade to HTTP/2 accepted.")
            else:
                print("Invalid request. Closing connection2.")
                client_socket.close()
                return

        settings_frame_handler(client_socket, client_address)

        #Transition to Frame Processor (not implemented yet)
        print("Handing over to Frame Processor...")
        # frame_processor(client_socket)

    except Exception as e:
        print(f"Error: {e}")
        client_socket.close()
    finally:
        if client_address in client_settings:
            del client_settings[client_address]
        client_socket.close()
        print(f"Connection with {client_address} closed and its settings deleted.")

def handle_client_thread(client_socket, client_address):
    handle_client_connection(client_socket, client_address)

def start_server(host="127.0.0.1", port=80):
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_socket.bind((host, port))
    server_socket.listen(10)
    print(f"Server is listening on {host}:{port}")

    try:
        while True:
            client_socket, client_address = server_socket.accept()
            print(f"Accepted connection from {client_address}")
            client_thread = threading.Thread(target=handle_client_thread, args=(client_socket, client_address))
            client_thread.start()
    except KeyboardInterrupt:
        print("Shutting down server...")
    finally:
        server_socket.close()

if __name__ == "__main__":
    start_server()
