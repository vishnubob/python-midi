
def read_varlen(data):
    has_next_byte = True
    value = 0
    while has_next_byte:
        char = next(data)
        # is the hi-bit set?
        if not (char & 0x80):
            # no next BYTE
            has_next_byte = False
        # mask out the 8th bit
        char = char & 0x7f
        # shift last value up 7 bits
        value = value << 7
        # add new value
        value += char
    return value


def write_varlen(value):
    result = bytearray()
    high_bit = 0
    while value > 0x7F:
        result.append((value & 0x7F) | high_bit)
        value >>= 7
        high_bit = 0x80
    result.append(value | high_bit)
    return result[::-1]
