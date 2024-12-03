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
            #handle_client_connection(client_socket)
    except KeyboardInterrupt:
        print("Shutting down server...")
    finally:
        server_socket.close()

if __name__ == "__main__":
    start_server()
