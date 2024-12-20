from enum import Enum
from Database import *
import struct

class StreamState(Enum):
    IDLE = "idle"
    RESERVED_LOCAL = "reserved (local)"
    RESERVED_REMOTE = "reserved (remote)"
    OPEN = "open"
    HALF_CLOSED_LOCAL = "half-closed (local)"
    HALF_CLOSED_REMOTE = "half-closed (remote)"
    CLOSED = "closed"

class Stream:
    def __init__(self, stream_id, client_address):
        self.stream_id = stream_id
        self.state = StreamState.IDLE
        self.client_address = client_address
        self.size = client_settings[client_address][0x4]

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

class StreamManager:
    def __init__(self):
        pass

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
                    # send GOAWAY frame
                    GOAWAY_FRAME_TYPE = 0x7
                    GOAWAY_NO_ERROR = 0x0
                    GOAWAY_STREAM_ID = 0x0
                    GOAWAY_PAYLOAD = b""
                    GOAWAY_FRAME = (struct.pack("!I", len(GOAWAY_PAYLOAD))[1:] + struct.pack("!B", GOAWAY_FRAME_TYPE) + struct.pack("!B", 0) + struct.pack("!I", GOAWAY_STREAM_ID) + GOAWAY_PAYLOAD)
                    socket.sendall(GOAWAY_FRAME)
        stream = streams[stream_id]
        if (frame.get_frame_type() == 0x0) or (frame.get_frame_type() == 0x1): # DATA frame or HEADERS frame
                if frame.get_frame_type() == 0x0: # DATA frame
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
                        # send update window frame by incerement value = 65535
                        WINDOW_UPDATE_STREAM_ID = stream_id
                        WINDOW_UPDATE_FRAME = (struct.pack("!I", len(WINDOW_UPDATE_PAYLOAD))[1:] + struct.pack("!B", WINDOW_UPDATE_FRAME_TYPE) + struct.pack("!B", 0) + struct.pack("!I", WINDOW_UPDATE_STREAM_ID) + WINDOW_UPDATE_PAYLOAD)
                        socket.sendall(WINDOW_UPDATE_FRAME)
                        stream.set_size(stream.get_size() + 65535)
                    if sizes_for_sockets[client_address] < decrement:
                        WINDOW_UPDATE_STREAM_ID = 0x0
                        WINDOW_UPDATE_FRAME = (struct.pack("!I", len(WINDOW_UPDATE_PAYLOAD))[1:] + struct.pack("!B", WINDOW_UPDATE_FRAME_TYPE) + struct.pack("!B", 0) + struct.pack("!I", WINDOW_UPDATE_STREAM_ID) + WINDOW_UPDATE_PAYLOAD)
                        socket.sendall(WINDOW_UPDATE_FRAME)
                        sizes_for_sockets[client_address] += 65535
                if 0x1 & frame.get_frame_flags(): # END_STREAM flag
                    if frame.get_server_initiated():
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