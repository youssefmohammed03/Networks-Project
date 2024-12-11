# ----------------------------------------- Static Table -------------------------------------------------#

static_table = [
    ("", ""),                          # Index 0
    (":authority", ""),                # Index 1
    (":method", "GET"),                # Index 2
    (":method", "POST"),               # Index 3
    (":path", "/"),                    # Index 4
    (":path", "/index.html"),          # Index 5
    (":scheme", "http"),               # Index 6
    (":scheme", "https"),              # Index 7
    (":status", "200"),                # Index 8
    (":status", "204"),                # Index 9
    (":status", "206"),                # Index 10
    (":status", "304"),                # Index 11
    (":status", "400"),                # Index 12
    (":status", "404"),                # Index 13
    (":status", "500"),                # Index 14
    ("accept-charset", ""),            # Index 15
    ("accept-encoding", "gzip, deflate"), # Index 16
    ("accept-language", ""),           # Index 17
    ("accept-ranges", ""),             # Index 18
    ("accept", ""),                    # Index 19
    ("access-control-allow-origin", ""), # Index 20
    ("age", ""),                       # Index 21
    ("allow", ""),                     # Index 22
    ("authorization", ""),             # Index 23
    ("cache-control", ""),             # Index 24
    ("content-disposition", ""),       # Index 25
    ("content-encoding", ""),          # Index 26
    ("content-language", ""),          # Index 27
    ("content-length", ""),            # Index 28
    ("content-location", ""),          # Index 29
    ("content-range", ""),             # Index 30
    ("content-type", ""),              # Index 31
    ("cookie", ""),                    # Index 32
    ("date", ""),                      # Index 33
    ("etag", ""),                      # Index 34
    ("expect", ""),                    # Index 35
    ("expires", ""),                   # Index 36
    ("from", ""),                      # Index 37
    ("host", ""),                      # Index 38
    ("if-match", ""),                  # Index 39
    ("if-modified-since", ""),         # Index 40
    ("if-none-match", ""),             # Index 41
    ("if-range", ""),                  # Index 42
    ("if-unmodified-since", ""),       # Index 43
    ("last-modified", ""),             # Index 44
    ("link", ""),                      # Index 45
    ("location", ""),                  # Index 46
    ("max-forwards", ""),              # Index 47
    ("proxy-authenticate", ""),        # Index 48
    ("proxy-authorization", ""),       # Index 49
    ("range", ""),                     # Index 50
    ("referer", ""),                   # Index 51
    ("refresh", ""),                   # Index 52
    ("retry-after", ""),               # Index 53
    ("server", ""),                    # Index 54
    ("set-cookie", ""),                # Index 55
    ("strict-transport-security", ""), # Index 56
    ("transfer-encoding", ""),         # Index 57
    ("user-agent", ""),                # Index 58
    ("vary", ""),                      # Index 59
    ("via", ""),                       # Index 60
    ("www-authenticate", "")           # Index 61
]
# ----------------------------------------- End of Static Table -------------------------------------------------#

# ------------------------------------ Dynamic Table Implementation ---------------------------------------------#

class DynamicTable:
    def __init__(self, max_size=4096):
        self.table = []
        self.current_size = 0
        self.max_size = max_size

    def add_entry(self, name, value):
        entry_size = len(name) + len(value) + 32

        while self.current_size + entry_size > self.max_size and self.table:
            evicted = self.table.pop(0)
            self.current_size -= len(evicted[0]) + len(evicted[1]) + 32

        self.table.append((name, value))
        self.current_size += entry_size

    def get_entry(self, index):
        if index == 0:
            raise ValueError("Invalid index")
        
        index -= 62

        if index > len(self.table):
            raise ValueError("Invalid index")
        
        return self.table[index]
    
    def clear_dynamic_table(self):
        self.table = []
        self.current_size = 0

    def get_max_size(self):
        return self.max_size
    
    def get_current_size(self):
        return self.current_size
    
    def get_table(self):
        return self.table
    
    def update_max_size(self, new_max_size):
        self.max_size = new_max_size

# ------------------------------------ End of Dynamic Table Implementation --------------------------------------#

#-----------------------------------------------Ecoding Functions------------------------------------------------#

def print_bytes_in_binary(byte_data):
    binary_strings = [bin(byte)[2:].zfill(8) for byte in byte_data]
    print(" ".join(binary_strings))

#make it return raw bytes b''
def print_binary_in_bytes(binary_string):
    byte_data = [int(binary_string[i:i+8], 2) for i in range(0, len(binary_string), 9)]
    print(byte_data)

def encode_integer(value, prefix_bits):
    max_prefix_value = (1 << prefix_bits) - 1
    if value < max_prefix_value:
        return bytes([value])
    else:
        result = [max_prefix_value]
        value -= max_prefix_value
        while value >= 128:
            result.append((value % 128) + 128)
            value //= 128
        result.append(value)
        return bytes(result)
    

def encode_string(string, huffman=False):
    """
    Encodes a string with optional Huffman encoding.
    """
    encoded = string.encode("utf-8")
    huffman_flag = 0x80 if huffman else 0x00
    length_encoded = encode_integer(len(encoded), 7)
    return bytes([length_encoded[0] | huffman_flag]) + length_encoded[1:] + encoded

def encode(dynamic_table, name, value, indexing = True):
    for i, (n, v) in enumerate(static_table):
        if n == name and v == value:
            encoded_byte = encode_integer(i, 7)
            return bytes([encoded_byte[0] | 0x80]) + encoded_byte[1:]

    for i, (n, v) in enumerate(dynamic_table.get_table()):
        if n == name and v == value:
            encoded_byte = encode_integer(i + 62, 7)
            return bytes([encoded_byte[0] | 0x80]) + encoded_byte[1:]

    for i, (n, v) in enumerate(static_table):
        if n == name:
            if indexing:
                encoded_byte = encode_integer(i, 6)
                encoded_name_index = bytes([encoded_byte[0] | 0x40]) + encoded_byte[1:]
                encoded_value = encode_string(value)
                dynamic_table.add_entry(name, value)
                return encoded_name_index + encoded_value
            else:
                encoded_name_index = encode_integer(i, 4)
                encoded_value = encode_string(value)
                return encoded_name_index + encoded_value

    for i, (n, v) in enumerate(dynamic_table.get_table()):
        if n == name:
            if indexing:
                encoded_byte = encode_integer(i + 62, 6)
                encoded_name_index = bytes([encoded_byte[0] | 0x40]) + encoded_byte[1:]
                encoded_value = encode_string(value)
                dynamic_table.add_entry(name, value)
                return encoded_name_index + encoded_value
            else:
                encoded_name_index = encode_integer(i + 62, 4)
                encoded_value = encode_string(value)
                return encoded_name_index + encoded_value

    encoded_name = encode_string(name)
    encoded_value = encode_string(value)
    if indexing:
        dynamic_table.add_entry(name, value)
        encoded_byte = encode_integer(0, 6)
        flag = bytes([encoded_byte[0] | 0x40]) + encoded_byte[1:]
        return flag + encoded_name + encoded_value
    else:
        flag = encode_integer(0, 4)
        return flag + encoded_name + encoded_value

#-------------------------------------------End of Encoding Functions--------------------------------------------#

#-----------------------------------------------Decoding Functions-----------------------------------------------#

def decode_integer(data, prefix_bits):
    """
    Decodes an integer from the HPACK variable-length encoding.
    """
    mask = (1 << prefix_bits) - 1 
    value = data[0] & mask  
    if value < mask:  
        return value, 1

    value = mask
    shift = 0
    i = 1
    while True:
        B = data[i] 
        value += (B & 0x7F) << shift  
        shift += 7
        if not (B & 0x80):
            break
        i += 1

    return value, i + 1


def decode_string(data):
    """
    Decodes a string from HPACK format.
    """
    huffman = data[0] & 0x80
    length, consumed = decode_integer(data, 7)
    string = data[consumed:consumed + length].decode("utf-8")
    return string, consumed + length

def decode(dynamic_table, data):
    headers = []
    i = 0
    while i < len(data):
        byte = data[i]
        if byte & 0x80: # Index Representation
            index, consumed = decode_integer(data[i:], 7)
            i += consumed
            if index < 62:
                name, value = static_table[index]
            else:
                name, value = dynamic_table.get_entry(index)
            headers.append((name, value))

        elif byte & 0x40:
            index, consumed = decode_integer(data[i:], 6)
            if index == 0: # New Name Incremental Indexing
                i += consumed
                name, consumed = decode_string(data[i:])
                i += consumed
                value, consumed = decode_string(data[i:])
                i += consumed
                dynamic_table.add_entry(name, value)
                headers.append((name, value))
            elif index: # Indexed Name Incremental Indexing
                i += consumed
                if index < 62:
                    name, _ = static_table[index]
                else:
                    name, _ = dynamic_table.get_entry(index)
                value, consumed = decode_string(data[i:])
                i += consumed
                dynamic_table.add_entry(name, value)
                headers.append((name, value))
            else:
                return headers

        elif byte & 0x00:
            index, consumed = decode_integer(data[i:], 4)
            if index == 0: #New Name without Incremental Indexing
                i += consumed
                name, consumed = decode_string(data[i:])
                i += consumed
                value, consumed = decode_string(data[i:])
                i += consumed
                headers.append((name, value))
            elif index: #Indexed Name without Incremental Indexing
                i += consumed
                if index < 62:
                    name, _ = static_table[index]
                else:
                    name, _ = dynamic_table.get_entry(index)
                value, consumed = decode_string(data[i:])
                i += consumed
                headers.append((name, value))
            else:
                return headers

        elif byte & 0x10:
            index, consumed = decode_integer(data[i:], 4)
            if index == 0: #New Name Never Incremental Indexing
                i += consumed
                name, consumed = decode_string(data[i:])
                i += consumed
                value, consumed = decode_string(data[i:])
                i += consumed
                headers.append((name, value))
            elif index: #Indexed Name Never Incremental Indexing
                i += consumed
                if index < 62:
                    name, _ = static_table[index]
                else:
                    name, _ = dynamic_table.get_entry(index)
                value, consumed = decode_string(data[i:])
                i += consumed
                headers.append((name, value))
            else:
                return headers
        elif byte & 0x20: #Update Dynamic Table Max Size
            index, consumed = decode_integer(data[i:], 5)
            i += consumed
            dynamic_table.update_max_size(index)

        else:
            return headers

    return headers

#-------------------------------------------End of Decoding Functions--------------------------------------------#

#-----------------------------------------------Testing Functions------------------------------------------------#

dt_for_server = DynamicTable()
dt_for_client = DynamicTable()
from_client_to_server = [
    (":method", "GET"),
    (":scheme", "https"),
    (":path", "/"),
    (":authority", "www.example.com"),
    ("name1", "value1"),
    ("name2", "value2"),
    ("name3", "value3")
]

encoded_headers = b""
for name, value in from_client_to_server:
    encoded_headers += encode(dt_for_client, name, value)

print("Encoded Headers", encoded_headers)
print("Decoded Headers:", decode(dt_for_server, encoded_headers))
print("Dynamic Table for Client:", dt_for_client.get_table())
print("Dynamic Table for Server:", dt_for_server.get_table())


#--------------------------------------------End of Testing Functions--------------------------------------------#