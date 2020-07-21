
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
    while value > 0x7F:
        result.append((value & 0x7F) | 0x80)
        value >>= 7
    result.append(value)
    return result
