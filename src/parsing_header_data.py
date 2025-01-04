from frames import *
from Database import *
from stream_manager import *
from website import *
from stream_manager import *
import HPACK as hpack

web = SimpleWebsite()

def remove_data_padding(frame):
    if frame.get_frame_flags() & 0x8:
        padding_length = frame.get_payload()[0] + 1
        return frame.get_payload()[1:-padding_length]
    else:
        return frame.get_payload()
    
def get_header_block_fragment(frame):
    payload = frame.get_payload()
    flags = frame.get_frame_flags()
    offset = 0
    if flags & 0x8:  
        pad_length = payload[offset]
        offset += 1
    else:
        pad_length = 0
    if flags & 0x20:  
        offset += 5  
    header_block_end = len(payload) - pad_length
    header_block_fragment = payload[offset:header_block_end]

    return header_block_fragment

def parse_headers_frame(frame, client_address, stream_id, socket):
    header_block_fragment = get_header_block_fragment(frame)
    headers = hpack.decode(client_dynamic_table[client_address], header_block_fragment)
    stream = streams[frame.get_stream_id()]
    headers = dict(headers)
    stream.set_request_header(headers)
    if frame.get_frame_flags() & 0x1: # END_STREAM
        headers, data = web.handle_request(headers, 0)
        construct_response(headers, data, client_address, stream_id, socket)

def parse_data_frame(frame, client_address, stream_id, socket):
    stream = streams[frame.get_stream_id()]
    stream.set_request_body(remove_data_padding(frame))
    if frame.get_frame_flags() & 0x1: # END_STREAM
        headers, data = web.handle_request(stream.get_request()["header"], stream.get_request()["body"])
        construct_response(headers, data, client_address, stream_id, socket)

def construct_response(headers, data, client_address, stream_id_resp, socket):
    header_block_fragment = b''
    for header in headers:
        header_block_fragment += hpack.encode(client_dynamic_table[client_address], header[0], header[1], indexing=False) # Remove indexing
    if data:
        header_frame_response = Frame(frame=None, server_initiated=True, header=header_block_fragment, end_stream=False, stream_id_resp=stream_id_resp)
    else:
        header_frame_response = Frame(frame=None, server_initiated=True, header=header_block_fragment, end_stream=True, stream_id_resp=stream_id_resp)
    streamManager.stream_manager(header_frame_response, client_address, socket)
    DEFAULT_FRAME_SIZE = 16384 

    for i in range(0, len(data), DEFAULT_FRAME_SIZE):
        if i + DEFAULT_FRAME_SIZE >= len(data):
            data_frame_response = Frame(
                frame=None,
                server_initiated=True,
                data=data[i:],  
                end_stream=True,  
                stream_id_resp=stream_id_resp
            )
        else:
            data_frame_response = Frame(
                frame=None,
                server_initiated=True,
                data=data[i:i + DEFAULT_FRAME_SIZE],  
                end_stream=False,  
                stream_id_resp=stream_id_resp
            )
        streamManager.stream_manager(data_frame_response, client_address, socket)