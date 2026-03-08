"""MIDI variable-length quantity encoding/decoding."""
from collections.abc import Iterator


def read_varlen(data: Iterator[int]) -> int:
    """Decode a MIDI variable-length quantity from a byte iterator.

    Args:
        data: Iterator yielding individual bytes.

    Returns:
        The decoded integer value.
    """
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
    """Encode an integer as a MIDI variable-length quantity.

    Args:
        value: Non-negative integer to encode.

    Returns:
        The encoded bytes.
    """
    result = [value & 0x7F]
    value >>= 7
    while value:
        result.append((value & 0x7F) | 0x80)
        value >>= 7
    return bytes(reversed(result))
