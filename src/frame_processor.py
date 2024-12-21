import socket
import struct
from connection_handler import *
import HPACK as hpack
from Database import *
import frames
from stream_manager import streamManager

def frame_processor(client_socket, client_address):
    try:
        while True:
            frame = frames.Frame(read_exact(client_socket, 9))
            frame.set_payload(read_exact(client_socket, frame.get_frame_length()))

            if frame.get_frame_type() == 0x0:  # DATA frame
                print("Data frame received")
                streamManager.stream_manager(frame, client_address, client_socket)
            elif frame.get_frame_type() == 0x1:  # HEADERS frame
                print("Headers frame received")
                streamManager.stream_manager(frame, client_address, client_socket)
                client_dynamic_table[client_address] = hpack.DynamicTable()
                headers = hpack.decode(client_dynamic_table[client_address], frame.get_payload())
                print(headers)
                print("Dynamic Table:", client_dynamic_table[client_address].get_table())
            elif frame.get_frame_type() == 0x2:  # PRIORITY frame
                print("Priority frame received")
            elif frame.get_frame_type() == 0x3:  # RST_STREAM frame
                streamManager.stream_manager(frame, client_address, client_socket)
            elif frame.get_frame_type() == 0x4:  # SETTINGS frame
                settings_frame_handler(client_socket, client_address, frame)
            elif frame.get_frame_type() == 0x6:  # Ping frame
                ping_ack_frame = frames.Frame(0, server_initiated=False, frame_type=0x6, frame_flags=0x1, stream_id=0, payload=frame.get_payload())
                client_socket.sendall(ping_ack_frame.get_whole_frame())
            elif frame.get_frame_type() == 0x7:  # GOAWAY frame
                last_stream_id, error_code, reason = struct.unpack("!I I", frame.get_payload()[:8])
                streamManager.close_stream(last_stream_id)
                client_socket.close()
            elif frame.get_frame_type() == 0x8:  # WINDOW_UPDATE frame
                pass
            else:
                print(f"Unknown frame type {frame.get_frame_type()} received. Ignoring.")

    except Exception as e:
        print(f"Error in frame processor for {client_address}: {e}")
        return
