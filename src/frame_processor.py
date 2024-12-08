import socket
import struct
from connection_handler import *

def frame_processor(client_socket, client_address):
    try:
        while True:
            frame_header = read_exact(client_socket, 9)
            frame_length, frame_type, frame_flags, stream_id = struct.unpack("!I B B I", b"\x00" + frame_header)
            frame_length &= 0x00FFFFFF
            stream_id &= 0x7FFFFFFF

            if frame_type == 0x0:  # DATA frame
                s#tream_manager(frame_flags, stream_id)
                pass
            elif frame_type == 0x1:  # HEADERS frame
                #HPACK(frame_flags, stream_id)
                pass
            elif frame_type == 0x4:  # SETTINGS frame
                settings_frame_handler(frame_flags, stream_id, client_address)
            elif frame_type == 0x8:  # WINDOW_UPDATE frame
                #flow_control(stream_id)
                pass
            elif frame_type == 0x3:  # RST_STREAM frame
                #handle_rst_stream_frame(stream_id)
                pass
            elif frame_type == 0x7:  # GOAWAY frame
                #handle_goaway_frame(client_socket)
                pass
            else:
                print(f"Unknown frame type {frame_type} received. Ignoring.")

    except Exception as e:
        print(f"Error in frame processor for {client_address}: {e}")
        client_socket.close()