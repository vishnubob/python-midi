import os
import tempfile
import midi


def _get_mary_pattern():
    """Build the Mary Had a Little Lamb test pattern."""
    return midi.Pattern(tracks=[
        [midi.TimeSignatureEvent(tick=0, data=[4, 2, 24, 8]),
         midi.KeySignatureEvent(tick=0, data=[0, 0]),
         midi.EndOfTrackEvent(tick=1, data=[])],
        [midi.ControlChangeEvent(tick=0, channel=0, data=[91, 58]),
         midi.ControlChangeEvent(tick=0, channel=0, data=[10, 69]),
         midi.ControlChangeEvent(tick=0, channel=0, data=[0, 0]),
         midi.ControlChangeEvent(tick=0, channel=0, data=[32, 0]),
         midi.ProgramChangeEvent(tick=0, channel=0, data=[24]),
         midi.NoteOnEvent(tick=0, channel=0, data=[64, 72]),
         midi.NoteOnEvent(tick=0, channel=0, data=[55, 70]),
         midi.NoteOnEvent(tick=231, channel=0, data=[64, 0]),
         midi.NoteOnEvent(tick=25, channel=0, data=[62, 72]),
         midi.NoteOnEvent(tick=231, channel=0, data=[62, 0]),
         midi.NoteOnEvent(tick=25, channel=0, data=[60, 71]),
         midi.NoteOnEvent(tick=231, channel=0, data=[60, 0]),
         midi.NoteOnEvent(tick=25, channel=0, data=[62, 79]),
         midi.EndOfTrackEvent(tick=1, data=[])]
    ])


class TestFileIO:
    def test_roundtrip_mary(self, tmp_path):
        mary = _get_mary_pattern()
        path = str(tmp_path / "mary.mid")
        midi.write_midifile(path, mary)
        pattern1 = midi.read_midifile(path)
        midi.write_midifile(path, pattern1)
        pattern2 = midi.read_midifile(path)
        assert len(pattern1) == len(pattern2)
        for track_idx in range(len(pattern1)):
            assert len(pattern1[track_idx]) == len(pattern2[track_idx])
            for event_idx in range(len(pattern1[track_idx])):
                event1 = pattern1[track_idx][event_idx]
                event2 = pattern2[track_idx][event_idx]
                assert event1.tick == event2.tick
                assert event1.data == event2.data

    def test_read_existing_file(self):
        data_dir = os.path.join(os.path.dirname(__file__), 'data')
        path = os.path.join(data_dir, 'mary.mid')
        if os.path.exists(path):
            pattern = midi.read_midifile(path)
            assert len(pattern) > 0

    def test_write_binary_io(self, tmp_path):
        mary = _get_mary_pattern()
        path = str(tmp_path / "test.mid")
        with open(path, 'wb') as f:
            midi.write_midifile(f, mary)
        pattern = midi.read_midifile(path)
        assert len(pattern) == 2

    def test_read_binary_io(self, tmp_path):
        mary = _get_mary_pattern()
        path = str(tmp_path / "test.mid")
        midi.write_midifile(path, mary)
        with open(path, 'rb') as f:
            pattern = midi.read_midifile(f)
        assert len(pattern) == 2
