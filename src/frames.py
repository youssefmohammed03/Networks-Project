import struct

class Frame:
    frame_length = 0
    frame_type = 0
    frame_flags = 0x0
    stream_id = 0
    payload = b""
    server_initiated = False
    whole_frame = b""
    def __init__(self, frame, server_initiated=False, rst_stream=False, goaway=False, last_stream_id=0, error_code=0, reason=""):
        if server_initiated:
            if rst_stream:
                self.frame_length = 8  
                self.frame_type = 0x3  
                self.frame_flags = 0   
                self.stream_id = last_stream_id  
                self.payload = struct.pack("!I", error_code)  
                whole_frame = struct.pack("!I", self.frame_length)[1:] + struct.pack("!B", self.frame_type) + struct.pack("!B", self.frame_flags) + struct.pack("!I", self.stream_id) + self.payload
            if goaway:
                self.frame_length = 8 + len(reason.encode('utf-8'))  
                self.frame_type = 0x7 
                self.frame_flags = 0   
                self.stream_id = 0     
                self.payload = struct.pack("!I", last_stream_id) + struct.pack("!I", error_code) + reason.encode("utf-8")
                whole_frame = struct.pack("!I", self.frame_length)[1:] + struct.pack("!B", self.frame_type) + struct.pack("!B", self.frame_flags) + struct.pack("!I", self.stream_id) + self.payload
        else:
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

    def get_whole_frame(self):
        return self.whole_frame