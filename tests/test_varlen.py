import midi


class TestVarlen:
    def test_roundtrip(self):
        maxval = 0x0FFFFFFF
        for inval in range(0, maxval, maxval // 1000):
            datum = midi.write_varlen(inval)
            outval = midi.read_varlen(iter(datum))
            assert inval == outval

    def test_zero(self):
        datum = midi.write_varlen(0)
        assert datum == b'\x00'
        assert midi.read_varlen(iter(datum)) == 0

    def test_single_byte_max(self):
        datum = midi.write_varlen(0x7F)
        assert datum == b'\x7f'
        assert midi.read_varlen(iter(datum)) == 0x7F

    def test_two_bytes(self):
        datum = midi.write_varlen(0x80)
        assert len(datum) == 2
        assert midi.read_varlen(iter(datum)) == 0x80

    def test_max_value(self):
        maxval = 0x0FFFFFFF
        datum = midi.write_varlen(maxval)
        assert midi.read_varlen(iter(datum)) == maxval
