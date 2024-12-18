import struct

class Frame:
    frame_length = 0
    frame_type = 0
    frame_flags = []
    stream_id = 0
    payload = b""
    server_initiated = False
    def __init__(self, frame, server_initiated=False):
        #unpack frame header
        frame_length, frame_type, frame_flags, stream_id = struct.unpack("!I B B I", b"\x00" + frame)
        self.frame_length = frame_length
        self.frame_type = frame_type
        self.frame_flags = frame_flags
        self.stream_id = stream_id
        self.server_initiated = server_initiated

    def __str__(self):
        return f"Frame Length: {self.frame_length}, Frame Type: {self.frame_type}, Frame Flags: {self.frame_flags}, Stream ID: {self.stream_id}, Payload: {self.payload}"

    def __repr__(self):
        return f"Frame Length: {self.frame_length}, Frame Type: {self.frame_type}, Frame Flags: {self.frame_flags}, Stream ID: {self.stream_id}, Payload: {self.payload}"
    
    def get_frame_length(self):
        return self.frame_length
    
    def get_frame_type(self):
        return self.frame_type
    
    def get_frame_flags(self):
        return self.frame_flags
    
    def get_stream_id(self):
        return self.stream_id
    
    def get_payload(self):
        return self.payload
    
    def get_server_initiated(self):
        return self.server_initiated
    
    def set_payload(self, payload):
        self.payload = payload
