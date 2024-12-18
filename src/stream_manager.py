from enum import Enum
from Database import streams

class StreamState(Enum):
    IDLE = "idle"
    RESERVED_LOCAL = "reserved (local)"
    RESERVED_REMOTE = "reserved (remote)"
    OPEN = "open"
    HALF_CLOSED_LOCAL = "half-closed (local)"
    HALF_CLOSED_REMOTE = "half-closed (remote)"
    CLOSED = "closed"

class Stream:
    def __init__(self, stream_id):
        self.stream_id = stream_id
        self.state = StreamState.IDLE

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

class StreamManager:
    def __init__(self):
        pass

    def stream_manager(self, frame):
        stream_id = frame.get_stream_id()
        if stream_id not in streams:
            streams[stream_id] = Stream(stream_id)
        stream = streams[stream_id]
        if (frame.get_frame_type() == 0x0) or (frame.get_frame_type() == 0x1): # DATA frame or HEADERS frame
                if 0x1 in frame.get_frame_flags(): # END_STREAM flag
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
        elif frame.get_frame_type() == 0x1 and (0x1 not in frame.get_frame_flags()): # HEADERS frame without END_STREAM flag
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
        elif frame.get_frame_type() == 0x5 and (0x1 not in frame.get_frame_flags()): # PUSH_PROMISE frame without END_HEADERS flag
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