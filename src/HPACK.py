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
    def __init__(self, max_size=100):
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

# ------------------------------------ End of Dynamic Table Implementation --------------------------------------#