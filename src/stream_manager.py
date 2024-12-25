from enum import Enum
from Database import *
import struct
import error_handling as error

DEFAULT_FRAME_SIZE = 16384 

class StreamState(Enum):
    IDLE = "idle"
    RESERVED_LOCAL = "reserved (local)"
    RESERVED_REMOTE = "reserved (remote)"
    OPEN = "open"
    HALF_CLOSED_LOCAL = "half-closed (local)"
    HALF_CLOSED_REMOTE = "half-closed (remote)"
    CLOSED = "closed"

class Stream:
    request={}
    request["header"] = {}
    request["body"] = b""
    response={}
    response["header"] = {}
    response["body"] = b""
    def __init__(self, stream_id, client_address):
        self.stream_id = stream_id
        self.state = StreamState.IDLE
        self.client_address = client_address
        self.size = 65535
        self.size_for_client = client_settings[client_address][0x4]

    def __str__(self):
        return f"Stream ID: {self.stream_id}, State: {self.state}"

    def __repr__(self):
        return f"Stream ID: {self.stream_id}, State: {self.state}"

    def get_stream_id(self):
        return self.stream_id

    def get_state(self):
        return self.state

    def set_state(self, state):
        self.state = state
    
    def get_client_address(self):
        return self.client_address
    
    def set_client_address(self, client_address):
        self.client_address = client_address

    def get_size(self):
        return self.size
    
    def set_size(self, size):
        self.size = size
    
    def get_size_for_client(self):
        return self.size_for_client
    
    def set_size_for_client(self, size_for_client):
        self.size_for_client = size_for_client

    def get_request(self):
        return self.request
    
    def set_request_header(self, request):
        self.request["header"] = request

    def set_request_body(self, request):
        self.request["body"] = self.request["body"] + request

    def get_response(self):
        return self.response
    
    def set_response_header(self, response):
        self.response["header"] = response

    def set_response_body(self, response):
        self.response["body"] = self.response["body"] + response

class StreamManager:
    def __init__(self):
        pass

    def close_stream(self, stream_id):
        stream = streams[stream_id]
        stream.set_state(StreamState.CLOSED)

    def stream_manager(self, frame, client_address, socket):
        stream_id = frame.get_stream_id()
        if stream_id not in streams:
            if stream_id % 2 == 0: # server initiated
                MAX_CONCURRENT_STREAMS = client_settings[client_address][0x3]
                count = 0
                for stream in streams:
                    if stream_id % 2 == 0 and streams[stream].get_state() in [StreamState.OPEN, StreamState.HALF_CLOSED_REMOTE, StreamState.HALF_CLOSED_LOCAL] and streams[stream].get_client_address() == client_address:
                        count += 1
                if count <= MAX_CONCURRENT_STREAMS:
                    streams[stream_id] = Stream(stream_id, client_address)
                else:
                    raise Exception("Maximum concurrent streams exceeded.")
                    return
            else: # client initiated
                MAX_CONCURRENT_STREAMS = 100
                count = 0
                for stream in streams:
                    if stream_id % 2 != 0 and streams[stream].get_state() in [StreamState.OPEN, StreamState.HALF_CLOSED_REMOTE, StreamState.HALF_CLOSED_LOCAL] and streams[stream].get_client_address() == client_address:
                        count += 1
                if count <= MAX_CONCURRENT_STREAMS:
                    streams[stream_id] = Stream(stream_id, client_address)
                else:
                    error.handle_stream_error(stream_id, error.HTTP2ErrorCodes.REFUSED_STREAM, socket, client_address, reason="Maximum concurrent streams exceeded.")
        stream = streams[stream_id]
        if (frame.get_frame_type() == 0x0) or (frame.get_frame_type() == 0x1): # DATA frame or HEADERS frame
                if frame.get_frame_type() == 0x1: # Header frame
                    if frame.get_server_initiated() and frame.get_frame_flags() & 0x4:
                        stream.set_response_header(frame.get_payload())
                        socket.sendall(frame.get_whole_frame())
                        print("Header Frame sent for stream ID:", stream_id)
                if frame.get_frame_type() == 0x0: # DATA frame
                    if frame.get_server_initiated() and frame.get_frame_flags() & 0x0: # No END_STREAM flag
                        stream.set_response_body(frame.get_payload())
                        """ for i in range(2):
                            if (DEFAULT_FRAME_SIZE > sizes_for_sockets_for_clients[client_address]) or DEFAULT_FRAME_SIZE > stream.get_size_for_client():
                                frame_header = read_exact(socket, 9)
                                frame_length, frame_type, frame_flags, stream_id_window = struct.unpack("!I B B I", b"\x00" + frame_header)
                                frame_payload = read_exact(socket, frame_length)
                                if frame_type == 0x8: 
                                    if stream_id_window == 0:
                                        WINDOW_UPDATE_INCREMENT = struct.unpack("!I", frame_payload)[0]
                                        sizes_for_sockets_for_clients[client_address] += WINDOW_UPDATE_INCREMENT
                                    if stream_id_window == stream_id:
                                        WINDOW_UPDATE_INCREMENT = struct.unpack("!I", frame_payload)[0]
                                        stream.set_size_for_client(stream.get_size_for_client() + WINDOW_UPDATE_INCREMENT) """
                        socket.sendall(frame.get_whole_frame())
                        print("Data Frame sent for stream ID:", stream_id)
                        """ stream.set_size_for_client(stream.get_size_for_client() - len(frame.get_payload()))
                        sizes_for_sockets_for_clients[client_address] -= len(frame.get_payload()) """
                    if frame.get_frame_flags() & 0x8:
                        padding_length = frame.get_payload()[0] + 1
                        decrement = (len(frame.get_payload()) - padding_length)
                        stream.set_size(stream.get_size() - decrement)
                        sizes_for_sockets[client_address] -= decrement
                    else:
                        decrement = len(frame.get_payload())
                        stream.set_size(stream.get_size() - decrement)
                        sizes_for_sockets[client_address] -= decrement
                    WINDOW_UPDATE_FRAME_TYPE = 0x8
                    WINDOW_UPDATE_INCREMENT = 0xFFFF
                    WINDOW_UPDATE_PAYLOAD = struct.pack("!I", WINDOW_UPDATE_INCREMENT)
                    if stream.get_size() < decrement:
                        WINDOW_UPDATE_STREAM_ID = stream_id
                        WINDOW_UPDATE_FRAME = (struct.pack("!I", len(WINDOW_UPDATE_PAYLOAD))[1:] + struct.pack("!B", WINDOW_UPDATE_FRAME_TYPE) + struct.pack("!B", 0) + struct.pack("!I", WINDOW_UPDATE_STREAM_ID) + WINDOW_UPDATE_PAYLOAD)
                        socket.sendall(WINDOW_UPDATE_FRAME)
                        print("Window Update Frame sent for stream level for stream ID:", stream_id)
                        stream.set_size(stream.get_size() + 65535)
                    if sizes_for_sockets[client_address] < decrement:
                        WINDOW_UPDATE_STREAM_ID = 0x0
                        WINDOW_UPDATE_FRAME = (struct.pack("!I", len(WINDOW_UPDATE_PAYLOAD))[1:] + struct.pack("!B", WINDOW_UPDATE_FRAME_TYPE) + struct.pack("!B", 0) + struct.pack("!I", WINDOW_UPDATE_STREAM_ID) + WINDOW_UPDATE_PAYLOAD)
                        socket.sendall(WINDOW_UPDATE_FRAME)
                        print("Window Update Frame sent for connection level for client address:", client_address)
                        sizes_for_sockets[client_address] += 65535
                if 0x1 & frame.get_frame_flags(): # END_STREAM flag
                    if frame.get_server_initiated():
                        if frame.get_frame_type() == 0x0: # DATA frame
                            stream.set_response_body(frame.get_payload())
                            socket.sendall(frame.get_whole_frame())
                            print("Data Frame sent for stream ID:", stream_id)
                        if frame.get_frame_type() == 0x1: # HEADERS frame
                            stream.set_response_header(frame.get_payload())
                            socket.sendall(frame.get_whole_frame())
                            print("Header Frame sent for stream ID:", stream_id)
                        if stream.get_state() == StreamState.OPEN:
                            stream.set_state(StreamState.HALF_CLOSED_REMOTE)
                        elif stream.get_state() == StreamState.HALF_CLOSED_LOCAL:
                            stream.set_state(StreamState.CLOSED)
                    else:
                        if stream.get_state() == StreamState.OPEN:
                            stream.set_state(StreamState.HALF_CLOSED_LOCAL)
                        elif stream.get_state() == StreamState.HALF_CLOSED_REMOTE:
                            stream.set_state(StreamState.CLOSED)
        elif frame.get_frame_type() == 0x1 and (0x1 & frame.get_frame_flags() == 0): # HEADERS frame without END_STREAM flag
            if frame.get_server_initiated():
                stream.set_response_header(frame.get_payload())
                socket.sendall(frame.get_whole_frame())
                if stream.get_state() == StreamState.IDLE:
                    stream.set_state(StreamState.OPEN)
                elif stream.get_state() == StreamState.RESERVED_REMOTE:
                    stream.set_state(StreamState.HALF_CLOSED_LOCAL)
            else:
                if stream.get_state() == StreamState.IDLE:
                    stream.set_state(StreamState.OPEN)
                elif stream.get_state() == StreamState.RESERVED_LOCAL:
                    stream.set_state(StreamState.HALF_CLOSED_REMOTE)
        elif frame.get_frame_type() == 0x5 and (0x1 & frame.get_frame_flags()==0): # PUSH_PROMISE frame without END_HEADERS flag
            if frame.get_server_initiated():
                if stream.get_state() == StreamState.IDLE:
                    stream.set_state(StreamState.RESERVED_REMOTE)
            else:
                if stream.get_state() == StreamState.IDLE:
                    stream.set_state(StreamState.RESERVED_LOCAL)
        elif frame.get_frame_type() == 0x3: # RST_STREAM frame  
            if stream.get_state() == StreamState.OPEN:
                stream.set_state(StreamState.CLOSED)
            elif stream.get_state() == StreamState.HALF_CLOSED_LOCAL:
                stream.set_state(StreamState.CLOSED)
            elif stream.get_state() == StreamState.HALF_CLOSED_REMOTE:
                stream.set_state(StreamState.CLOSED)
            elif stream.get_state() == StreamState.RESERVED_LOCAL:
                stream.set_state(StreamState.CLOSED)
            elif stream.get_state() == StreamState.RESERVED_REMOTE:
                stream.set_state(StreamState.CLOSED)


streamManager = StreamManager()