import socket
import struct
from connection_handler import *
import HPACK as hpack
from Database import *
import frames
from stream_manager import *
from parsing_header_data import *
from logger_setup import get_logger

logger = get_logger()

def frame_processor(client_socket, client_address):
    try:
        while True:
            frame = frames.Frame(read_exact(client_socket, 9))
            frame.set_payload(read_exact(client_socket, frame.get_frame_length()))

            if frame.get_frame_type() == 0x0:  # DATA frame
                logger.info("Data frame received")
                streamManager.stream_manager(frame, client_address, client_socket)
                parse_data_frame(frame, client_address, frame.get_stream_id(), client_socket)
            elif frame.get_frame_type() == 0x1:  # HEADERS frame
                logger.info("Headers frame received")
                streamManager.stream_manager(frame, client_address, client_socket)
                parse_headers_frame(frame, client_address, frame.get_stream_id(), client_socket)
            elif frame.get_frame_type() == 0x2:  # PRIORITY frame
                logger.info("Priority frame received")
            elif frame.get_frame_type() == 0x3:  # RST_STREAM frame
                logger.info("RST_STREAM frame received")
                streamManager.stream_manager(frame, client_address, client_socket)
            elif frame.get_frame_type() == 0x4:  # SETTINGS frame
                logger.info("Settings frame received")
                settings_frame_handler(client_socket, client_address, frame)
            elif frame.get_frame_type() == 0x6:  # Ping frame
                logger.info("Ping frame received")
                ping_ack_frame = frames.Frame(0, server_initiated=False, frame_type=0x6, frame_flags=0x1, stream_id=0, payload=frame.get_payload())
                client_socket.sendall(ping_ack_frame.get_whole_frame())
            elif frame.get_frame_type() == 0x7:  # GOAWAY frame
                logger.info("Goaway frame received")
                last_stream_id, error_code = struct.unpack("!I I", frame.get_payload()[:8])
                reason = frame.get_payload()[8:].decode("utf-8", errors="ignore")
                logger.info(f"Last Stream ID: {last_stream_id}")
                logger.info(f"Error Code: {error_code}")
                if reason:
                    logger.info(f"Reason: {reason}")
                else:
                    logger.info("No reason provided.")
                streamManager.close_stream(last_stream_id)
                client_socket.close()
            elif frame.get_frame_type() == 0x8:  # WINDOW_UPDATE frame
                #will be handled in stream_manager
                pass
            else:
                logger.info(f"Unknown frame type {frame.get_frame_type()} received. Ignoring.")

    except Exception as e:
        return
