import midi


class TestTrack:
    def test_create_empty(self):
        track = midi.Track()
        assert len(track) == 0

    def test_append(self):
        track = midi.Track()
        ev = midi.NoteOnEvent(tick=0, channel=0, data=[60, 100])
        track.append(ev)
        assert len(track) == 1
        assert track[0] is ev

    def test_slice(self):
        track = midi.Track()
        for i in range(5):
            track.append(midi.NoteOnEvent(tick=i))
        sliced = track[1:3]
        assert isinstance(sliced, midi.Track)
        assert len(sliced) == 2

    def test_sort(self):
        track = midi.Track()
        track.append(midi.NoteOnEvent(tick=200))
        track.append(midi.NoteOnEvent(tick=100))
        track.sort()
        assert track[0].tick == 100
        assert track[1].tick == 200

    def test_make_ticks_abs_rel(self):
        track = midi.Track()
        track.append(midi.NoteOnEvent(tick=100))
        track.append(midi.NoteOnEvent(tick=50))
        track.append(midi.NoteOnEvent(tick=50))
        track.make_ticks_abs()
        assert track[0].tick == 100
        assert track[1].tick == 150
        assert track[2].tick == 200
        track.make_ticks_rel()
        assert track[0].tick == 100
        assert track[1].tick == 50
        assert track[2].tick == 50

    def test_iter(self):
        track = midi.Track([midi.NoteOnEvent(tick=i) for i in range(3)])
        ticks = [ev.tick for ev in track]
        assert ticks == [0, 1, 2]


class TestPattern:
    def test_create_empty(self):
        pattern = midi.Pattern()
        assert len(pattern) == 0

    def test_create_with_tracks(self):
        t1 = midi.Track()
        t2 = midi.Track()
        pattern = midi.Pattern(tracks=[t1, t2])
        assert len(pattern) == 2

    def test_resolution(self):
        pattern = midi.Pattern(resolution=480)
        assert pattern.resolution == 480

    def test_slice(self):
        tracks = [midi.Track() for _ in range(5)]
        pattern = midi.Pattern(tracks=tracks)
        sliced = pattern[1:3]
        assert isinstance(sliced, midi.Pattern)
        assert len(sliced) == 2
        assert sliced.resolution == pattern.resolution

    def test_append_track(self):
        pattern = midi.Pattern()
        pattern.append(midi.Track())
        assert len(pattern) == 1
