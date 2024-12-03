import socket
import struct

# HTTP/2 Constants
HTTP2_PREFACE = b"PRI * HTTP/2.0\r\n\r\nSM\r\n\r\n"
SETTINGS_FRAME_TYPE = 0x4
SETTINGS_ACK_FLAG = 0x1

def build_settings_frame():
    """
    Build an initial SETTINGS frame to send to the server.
    """
    # Example settings payload: SETTINGS_HEADER_TABLE_SIZE = 4096
    settings_payload = struct.pack("!H I", 0x1, 4096)  # Identifier 0x1, Value 4096
    frame_length = len(settings_payload)

    settings_frame = (
        struct.pack("!I", frame_length)[1:]  # 3-byte length
        + struct.pack("!B", SETTINGS_FRAME_TYPE)  # Frame type: SETTINGS
        + struct.pack("!B", 0)  # No flags
        + struct.pack("!I", 0)  # Stream ID: 0
        + settings_payload  # Payload
    )
    return settings_frame

def parse_frame_header(frame_header):
    """
    Parse an HTTP/2 frame header.
    """
    frame_length, frame_type, frame_flags, stream_id = struct.unpack("!I B B I", b"\x00" + frame_header)
    frame_length = frame_length & 0x00FFFFFF  # Mask out the extra byte from the 24-bit length
    stream_id = stream_id & 0x7FFFFFFF  # Clear the reserved bit
    return frame_length, frame_type, frame_flags, stream_id

def send_ack_settings_frame(sock):
    """
    Sends an ACK SETTINGS frame to acknowledge the server's SETTINGS frame.
    """
    ack_frame = (
        struct.pack("!I", 0)[1:]  # Frame length: 0 (empty payload)
        + struct.pack("!B", SETTINGS_FRAME_TYPE)  # Frame type: SETTINGS
        + struct.pack("!B", SETTINGS_ACK_FLAG)  # Flags: ACK
        + struct.pack("!I", 0)  # Stream ID: 0
    )
    sock.sendall(ack_frame)
    print("Sent ACK SETTINGS frame to server.")


def testing_client(server_host="127.0.0.1", server_port=80):
    """
    Connect to the server and perform the following:
    - Establish a TCP connection (3-way handshake).
    - Send the HTTP/2 connection preface.
    - Send an initial SETTINGS frame.
    - Validate the ACK SETTINGS frame.
    - Validate the server's SETTINGS frame.
    """
    print("Starting testing client...")
    try:
        # Step 1: Establish a TCP connection
        sock = socket.create_connection((server_host, server_port))
        print(f"Connected to server at {server_host}:{server_port}")

        # Step 2: Send the HTTP/2 connection preface
        sock.sendall(HTTP2_PREFACE)
        print("Sent HTTP/2 preface.")

        # Step 3: Send the initial SETTINGS frame
        settings_frame = build_settings_frame()
        sock.sendall(settings_frame)
        print("Sent initial SETTINGS frame.")

        # Step 4: Wait for and validate the ACK SETTINGS frame
        frame_header = sock.recv(9)
        frame_length, frame_type, frame_flags, stream_id = parse_frame_header(frame_header)

        if frame_type != SETTINGS_FRAME_TYPE or frame_flags != SETTINGS_ACK_FLAG or stream_id != 0:
            raise ValueError("Invalid ACK SETTINGS frame received.")
        print("ACK SETTINGS frame received and validated.")

        # Step 5: Wait for and validate the server's SETTINGS frame
        frame_header = sock.recv(9)
        frame_length, frame_type, frame_flags, stream_id = parse_frame_header(frame_header)

        if frame_type != SETTINGS_FRAME_TYPE or frame_flags != 0 or stream_id != 0:
            raise ValueError("Invalid server SETTINGS frame received.")
        settings_payload = sock.recv(frame_length)
        print(f"Server SETTINGS frame received with payload: {settings_payload}")

        # Parse the server's SETTINGS frame payload (key-value pairs)
        for i in range(0, frame_length, 6):
            key, value = struct.unpack("!H I", settings_payload[i:i + 6])
            print(f"Server setting: ID={key}, Value={value}")

        # Send ACK for the server's SETTINGS frame
        send_ack_settings_frame(sock)

        print("Testing client completed successfully!")

    except Exception as e:
        print(f"Error during testing: {e}")
    finally:
        sock.close()
        print("Connection closed.")

if __name__ == "__main__":
    testing_client()
