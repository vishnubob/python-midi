
def read_varlen(data):
    NEXTBYTE = 1
    value = 0
    while NEXTBYTE:
        chr = next(data)
        # is the hi-bit set?
        if not (chr & 0x80):
            # no next BYTE
            NEXTBYTE = 0
        # mask out the 8th bit
        chr = chr & 0x7f
        # shift last value up 7 bits
        value = value << 7
        # add new value
        value += chr
    return value

def write_varlen(value):
    result = bytearray()
    hi_bit = 0
    while value > 0x7F:
        result.append((value & 0x7F) | hi_bit)
        value >>= 7
        hi_bit = 0x80
    result.append(value | hi_bit)
    return result[::-1]
