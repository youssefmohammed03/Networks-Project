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

def parse_headers_frame(frame, client_address):
    header_block_fragment = get_header_block_fragment(frame)
    client_dynamic_table[client_address] = hpack.DynamicTable()
    headers = hpack.decode(client_dynamic_table[client_address], header_block_fragment)
    stream = streams[frame.get_stream_id()]
    headers = dict(headers)
    stream.set_request_header(headers)
    if frame.get_frame_flags() & 0x1: # END_STREAM
        web.handle_request(headers, 0)
        return
    return

def parse_data_frame(frame):
    stream = streams[frame.get_stream_id()]
    stream.set_request_body(remove_data_padding(frame))
    if frame.get_frame_flags() & 0x1: # END_STREAM
        web.handle_request(stream.get_request()["header"], stream.get_request()["body"])
        return
    return

