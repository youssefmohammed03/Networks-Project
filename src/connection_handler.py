import socket
import struct

# Constants for HTTP/2
HTTP2_PREFACE = b"PRI * HTTP/2.0\r\n\r\nSM\r\n\r\n"
SETTINGS_FRAME_TYPE = 0x4  # Frame type for SETTINGS
CONNECTION_PREFACE_TIMEOUT = 5  # Timeout in seconds for client preface

def read_exact(sock, length):
    """Helper function to read an exact number of bytes from a socket."""
    data = b""
    while len(data) < length:
        chunk = sock.recv(length - len(data))
        if not chunk:
            raise ConnectionError("Connection closed by client.")
        data += chunk
    return data

def handle_client_connection(client_socket):
    """Handle an individual client connection for HTTP/2."""
    try:
        # Step 1: Read and validate the HTTP/2 connection preface
        preface = read_exact(client_socket, len(HTTP2_PREFACE))
        if preface != HTTP2_PREFACE:
            print("Invalid HTTP/2 preface received. Closing connection.")
            client_socket.close()
            return
        
        print("Valid HTTP/2 preface received.")

        # Step 2: Read and validate the client's initial SETTINGS frame
        # HTTP/2 frame header: 9 bytes
        frame_header = read_exact(client_socket, 9)
        frame_length, frame_type, frame_flags, stream_id = struct.unpack("!I B B I", b"\x00" + frame_header)
        
        # Validate frame type and stream ID
        if frame_type != SETTINGS_FRAME_TYPE or stream_id != 0:
            print("Invalid SETTINGS frame. Closing connection.")
            client_socket.close()
            return
        
        # Read and process the payload (frame_length bytes)
        settings_payload = read_exact(client_socket, frame_length)
        print("Initial SETTINGS frame received from client:", settings_payload)

        # Step 3: Send the server connection preface with a SETTINGS frame
        server_settings_payload = b""  # No specific settings for now
        server_settings_frame = (
            struct.pack("!I", len(server_settings_payload))[1:]  # 3 bytes length
            + struct.pack("!B", SETTINGS_FRAME_TYPE)  # Frame type
            + struct.pack("!B", 0)  # Flags
            + struct.pack("!I", 0)  # Stream ID
            + server_settings_payload  # Payload
        )
        client_socket.sendall(server_settings_frame)
        print("Server connection preface sent.")

        # Step 4: Transition to Frame Processor (not implemented yet)
        print("Handing over to Frame Processor...")
        # frame_processor(client_socket)

    except Exception as e:
        print(f"Error: {e}")
        client_socket.close()

def start_server(host="127.0.0.1", port=8080):
    """Start the HTTP/2 server."""
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_socket.bind((host, port))
    server_socket.listen(5)
    print(f"Server is listening on {host}:{port}")

    try:
        while True:
            client_socket, client_address = server_socket.accept()
            print(f"Accepted connection from {client_address}")
            handle_client_connection(client_socket)
    except KeyboardInterrupt:
        print("Shutting down server...")
    finally:
        server_socket.close()

if __name__ == "__main__":
    start_server()
