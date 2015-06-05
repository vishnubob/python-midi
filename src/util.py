
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
    b1 = value & 0x7F
    value >>= 7
    if value:
        b2 = (value & 0x7F) | 0x80
        value >>= 7
        if value:
            b3 = (value & 0x7F) | 0x80
            value >>= 7
            if value:
                b4 = (value & 0x7F) | 0x80
                res = bytes((b4,b3,b2,b1))
            else:
                res = bytes((b3,b2,b1))
        else:
            res = bytes((b2,b1))
    else:
        res = bytes((b1,))
    return res

