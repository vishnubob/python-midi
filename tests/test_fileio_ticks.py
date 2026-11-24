import midi
import pytest


@pytest.mark.parametrize("pattern", [
    # Plain event lists carry no mode of their own.
    midi.Pattern([[midi.EndOfTrackEvent(tick=180)]], tick_relative=False),
    # A track can be in absolute mode independently of its parent pattern.
    midi.Pattern([midi.Track(), midi.Track([midi.EndOfTrackEvent(tick=180)],
                                          tick_relative=False)]),
], ids=["absolute-pattern", "absolute-track"])
def test_reject_absolute_ticks_before_overwriting_file(tmp_path, pattern):
    path = tmp_path / "song.mid"
    path.write_bytes(b"original contents")

    with pytest.raises(ValueError, match="relative ticks"):
        midi.write_midifile(str(path), pattern)

    assert path.read_bytes() == b"original contents"
