import struct
import socket
from stream_manager import *
import frames
from logger_setup import get_logger

logger = get_logger()

class HTTP2ErrorCodes:
    NO_ERROR = 0x0            # Graceful shutdown
    PROTOCOL_ERROR = 0x1      # Protocol error detected
    INTERNAL_ERROR = 0x2      # Implementation fault
    FLOW_CONTROL_ERROR = 0x3  # Flow-control limits exceeded
    SETTINGS_TIMEOUT = 0x4    # Settings not acknowledged
    STREAM_CLOSED = 0x5       # Frame received for closed stream
    FRAME_SIZE_ERROR = 0x6    # Frame size incorrect
    REFUSED_STREAM = 0x7      # Stream not processed
    CANCEL = 0x8              # Stream cancelled
    COMPRESSION_ERROR = 0x9   # Compression state not updated
    CONNECT_ERROR = 0xa       # TCP connection error for CONNECT method
    ENHANCE_YOUR_CALM = 0xb   # Processing capacity exceeded
    INADEQUATE_SECURITY = 0xc # Negotiated TLS parameters inadequate
    HTTP_1_1_REQUIRED = 0xd   # Use of HTTP/1.1 required

class HTTP2Error(Exception):
    def __init__(self, error_code, message=""):
        self.error_code = error_code
        self.message = message
        super().__init__(f"HTTP/2 Error: {error_code} - {message}")

def handle_connection_error(stream_id, error_code, socket, reason=""):
    logger.info(f"[CONNECTION ERROR] Stream ID: {stream_id}, Error Code: {error_code}, Reason: {reason}")
    goaway_frame = construct_goaway_frame(stream_id, error_code, reason)
    send_frame(goaway_frame, socket)
    terminate_connection(socket)

def handle_stream_error(stream_id, error_code, socket, client_address, reason=""):
    logger.info(f"[STREAM ERROR] Stream ID: {stream_id}, Error Code: {error_code}, Reason: {reason}")
    rst_stream_frame = construct_rst_stream_frame(stream_id, error_code)
    send_frame(rst_stream_frame, socket)
    close_stream(rst_stream_frame, client_address, socket)

def construct_goaway_frame(last_stream_id, error_code, reason=""):
    goaway_frame = frames.Frame(0, server_initiated=True, goaway=True, last_stream_id=last_stream_id, error_code=error_code, reason=reason)
    return goaway_frame

def construct_rst_stream_frame(stream_id, error_code):
    rst_stream_frame = frames.Frame(0, server_initiated=True, rst_stream=True, last_stream_id=stream_id, error_code=error_code)
    return rst_stream_frame

def send_frame(frame, socket):
    socket.sendall(frame.get_whole_frame())
    logger.info(f"[SEND FRAME] {frame}")

def terminate_connection(socket):
    socket.close()
    logger.info("[CONNECTION TERMINATED]")

def close_stream(frame, client_address, socket):
    streamManager.stream_manager(frame, client_address, socket)
    logger.info(f"[STREAM CLOSED] Stream ID: {frame.get()}")
