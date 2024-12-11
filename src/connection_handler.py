import socket
import struct
import threading
import json
import frame_processor as fm

HTTP2_PREFACE = b"PRI * HTTP/2.0\r\n\r\nSM\r\n\r\n"
SETTINGS_FRAME_TYPE = 0x4
SETTINGS_ACK_FLAG = 0x1

client_settings = {}
client_dynamic_table = {}

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

        print(f"Setting Identifier: {setting_id} ({setting_name}) = {value}")

    return settings

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
    print("SETTINGS FRAME sent to client.")

def send_server_ack_settings_frame(client_socket):
    ack_settings_frame = (struct.pack("!I", 0)[1:] + struct.pack("!B", SETTINGS_FRAME_TYPE) + struct.pack("!B", SETTINGS_ACK_FLAG) + struct.pack("!I", 0))
    client_socket.sendall(ack_settings_frame)
    print("ACK SETTINGS FRAME sent to client.")

def store_client_settings(frame_length, settings_payload, client_address):
    for i in range(0, frame_length, 6):
        key, value = struct.unpack("!H I", settings_payload[i:i + 6])
        client_settings[client_address][key] = value 
    print(f"Stored settings for client.")

def client_ack_settings_frame(client_socket):
    ack_frame_header = read_exact(client_socket, 9)
    ack_frame_length, ack_frame_type, ack_frame_flags, ack_stream_id = struct.unpack("!I B B I", b"\x00" + ack_frame_header)
        
    if ack_frame_type != SETTINGS_FRAME_TYPE or ack_frame_flags != SETTINGS_ACK_FLAG or ack_stream_id != 0:
        print("Invalid ACK SETTINGS frame received. Closing connection.")
        return

    print("ACK SETTINGS FRAME received from client.")

def settings_frame_handler(client_socket, client_address, frame_header):
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
    print("SETTINGS FRAME received from client.")
    decode_settings_frame(settings_payload)
    
    store_client_settings(frame_length, settings_payload, client_address)

    #send_server_ack_settings_frame(client_socket)

    send_settings_frame(client_socket)

    client_ack_settings_frame(client_socket)

def print_bytes_in_binary(byte_data):
    binary_strings = [bin(byte)[2:].zfill(8) for byte in byte_data]
    print(" ".join(binary_strings))

def handle_client_connection(client_socket, client_address):
    try:
        client_settings[client_address] = {}

        preface = read_exact(client_socket, len(HTTP2_PREFACE))
        if preface != HTTP2_PREFACE:
            print("Invalid HTTP/2 preface received. Closing connection.")
            client_socket.close()
            return
        print("PREFACE received from the client.")

        frame_header = read_exact(client_socket, 9)
        settings_frame_handler(client_socket, client_address, frame_header)

        
        print("Handing over to Frame Processor")
        fm.frame_processor(client_socket, client_address)

    except Exception as e:
        print(f"Error: {e}")
        client_socket.close()
    finally:
        if client_address in client_settings:
            del client_settings[client_address]
            del client_dynamic_table[client_address]
        client_socket.close()
        print(f"Connection with {client_address} closed and its settings deleted.")

def handle_client_thread(client_socket, client_address):
    handle_client_connection(client_socket, client_address)

def start_server(host="192.168.1.12", port=80):
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