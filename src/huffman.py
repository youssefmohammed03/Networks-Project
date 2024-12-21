class HuffmanEncoder:
    def __init__(self, huffman_code_list: list[int], huffman_code_list_lengths: list[int]) -> None:
        self.huffman_code_list = huffman_code_list
        self.huffman_code_list_lengths = huffman_code_list_lengths

    def encode(self, bytes_to_encode: bytes) -> bytes:
        if not bytes_to_encode:
            return b''

        final_num = 0
        final_int_len = 0

        for byte in bytes_to_encode:
            bin_int_len = self.huffman_code_list_lengths[byte]
            bin_int = self.huffman_code_list[byte] & (
                2 ** (bin_int_len + 1) - 1
            )
            final_num <<= bin_int_len
            final_num |= bin_int
            final_int_len += bin_int_len

        bits_to_be_padded = (8 - (final_int_len % 8)) % 8
        final_num <<= bits_to_be_padded
        final_num |= (1 << bits_to_be_padded) - 1

        s = hex(final_num)[2:].rstrip('L')

        s = '0' + s if len(s) % 2 != 0 else s

        total_bytes = (final_int_len + bits_to_be_padded) // 8
        expected_digits = total_bytes * 2

        if len(s) != expected_digits:
            missing_digits = expected_digits - len(s)
            s = ('0' * missing_digits) + s

        return bytes.fromhex(s)
