import socket
import struct
from connection_handler import *

def frame_processor(client_socket, client_address):
    try:
        while True:
            # Step 1: Read and parse the frame header
            frame_header = read_exact(client_socket, 9)
            frame_length, frame_type, frame_flags, stream_id = struct.unpack("!I B B I", b"\x00" + frame_header)
            frame_length &= 0x00FFFFFF  # Mask to get the 24-bit length
            stream_id &= 0x7FFFFFFF    # Clear reserved bits

            # Step 2: Read the frame payload
            frame_payload = read_exact(client_socket, frame_length)

            # Step 3: Dispatch based on frame type
            if frame_type == 0x0:  # DATA frame
                handle_data_frame(frame_payload, frame_flags, stream_id)
            elif frame_type == 0x1:  # HEADERS frame
                handle_headers_frame(frame_payload, frame_flags, stream_id)
            elif frame_type == 0x4:  # SETTINGS frame
                handle_settings_frame(frame_payload, frame_flags, stream_id, client_address)
            elif frame_type == 0x8:  # WINDOW_UPDATE frame
                handle_window_update_frame(frame_payload, stream_id)
            elif frame_type == 0x6:  # PING frame
                handle_ping_frame(frame_payload, frame_flags, client_socket)
            elif frame_type == 0x3:  # RST_STREAM frame
                handle_rst_stream_frame(frame_payload, stream_id)
            elif frame_type == 0x7:  # GOAWAY frame
                handle_goaway_frame(frame_payload, client_socket)
            else:
                print(f"Unknown frame type {frame_type} received. Ignoring.")

    except Exception as e:
        print(f"Error in frame processor for {client_address}: {e}")
        client_socket.close()

# Placeholder handlers for frame types
def handle_data_frame(payload, flags, stream_id):
    print(f"DATA frame received on stream {stream_id}, flags: {flags}, payload: {payload}")

def handle_headers_frame(payload, flags, stream_id):
    print(f"HEADERS frame received on stream {stream_id}, flags: {flags}, payload: {payload}")
    # Decompress headers using HPACK here

def handle_settings_frame(payload, flags, stream_id, client_address):
    if flags == SETTINGS_ACK_FLAG:
        print("ACK SETTINGS frame received.")
    else:
        print(f"SETTINGS frame received: {payload} for client {client_address}")

def handle_window_update_frame(payload, stream_id):
    window_increment = struct.unpack("!I", payload)[0]
    print(f"WINDOW_UPDATE received for stream {stream_id}, increment: {window_increment}")

def handle_ping_frame(payload, flags, client_socket):
    if flags == 0x1:  # ACK
        print("PING ACK received.")
    else:
        print("PING received, sending ACK.")
        ping_ack_frame = struct.pack("!I", len(payload))[1:] + struct.pack("!B", 0x6) + struct.pack("!B", 0x1) + struct.pack("!I", 0) + payload
        client_socket.sendall(ping_ack_frame)

def handle_rst_stream_frame(payload, stream_id):
    error_code = struct.unpack("!I", payload)[0]
    print(f"RST_STREAM received for stream {stream_id}, error code: {error_code}")

def handle_goaway_frame(payload, client_socket):
    last_stream_id, error_code = struct.unpack("!I I", payload[:8])
    print(f"GOAWAY received. Last stream ID: {last_stream_id}, Error code: {error_code}")
    client_socket.close()
