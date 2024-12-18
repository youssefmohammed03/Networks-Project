import socket
import struct
from connection_handler import *
import HPACK as hpack
from Database import *
import frames

def frame_processor(client_socket, client_address):
    try:
        while True:
            frame = frames.Frame(read_exact(client_socket, 9))
            frame.set_payload(read_exact(client_socket, frame.get_frame_length()))

            if frame.get_frame_type() == 0x0:  # DATA frame
                #stream_manager(frame_flags, stream_id)
                pass
            elif frame.get_frame_type() == 0x1:  # HEADERS frame
                client_dynamic_table[client_address] = hpack.DynamicTable()
                headers = hpack.decode(client_dynamic_table[client_address], frame.get_payload())
                print(headers)
            elif frame.get_frame_type() == 0x4:  # SETTINGS frame
                settings_frame_handler(client_socket, client_address, frame)
            elif frame.get_frame_type() == 0x8:  # WINDOW_UPDATE frame
                #flow_control(stream_id)
                pass
            elif frame.get_frame_type() == 0x3:  # RST_STREAM frame
                #handle_rst_stream_frame(stream_id)
                pass
            elif frame.get_frame_type() == 0x7:  # GOAWAY frame
                #handle_goaway_frame(client_socket)
                pass
            else:
                print(f"Unknown frame type {frame.get_frame_type()} received. Ignoring.")

    except Exception as e:
        print(f"Error in frame processor for {client_address}: {e}")
        client_socket.close()
