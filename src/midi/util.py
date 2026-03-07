from collections.abc import Iterator


def read_varlen(data: Iterator[int]) -> int:
    NEXTBYTE = 1
    value = 0
    while NEXTBYTE:
        byte = next(data)
        # is the hi-bit set?
        if not (byte & 0x80):
            # no next BYTE
            NEXTBYTE = 0
        # mask out the 8th bit
        byte = byte & 0x7f
        # shift last value up 7 bits
        value = value << 7
        # add new value
        value += byte
    return value


def write_varlen(value: int) -> bytes:
    b1 = bytes([value & 0x7F])
    value >>= 7
    if value:
        b2 = bytes([(value & 0x7F) | 0x80])
        value >>= 7
        if value:
            b3 = bytes([(value & 0x7F) | 0x80])
            value >>= 7
            if value:
                b4 = bytes([(value & 0x7F) | 0x80])
                res = b4 + b3 + b2 + b1
            else:
                res = b3 + b2 + b1
        else:
            res = b2 + b1
    else:
        res = b1
    return res
