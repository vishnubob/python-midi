import midi


class TestEvents:
    def test_note_on_event(self):
        ev = midi.NoteOnEvent(tick=100, channel=1, data=[60, 100])
        assert ev.tick == 100
        assert ev.channel == 1
        assert ev.pitch == 60
        assert ev.velocity == 100

    def test_note_off_event(self):
        ev = midi.NoteOffEvent(tick=200, channel=0, data=[60, 0])
        assert ev.pitch == 60
        assert ev.velocity == 0

    def test_control_change_event(self):
        ev = midi.ControlChangeEvent(channel=0, data=[7, 100])
        assert ev.control == 7
        assert ev.value == 100

    def test_program_change_event(self):
        ev = midi.ProgramChangeEvent(channel=0, data=[42])
        assert ev.value == 42

    def test_channel_after_touch_event(self):
        ev = midi.ChannelAfterTouchEvent(channel=0, data=[64])
        assert ev.value == 64

    def test_pitch_wheel_event(self):
        ev = midi.PitchWheelEvent(channel=0)
        ev.pitch = 0
        assert ev.pitch == 0
        ev.pitch = 1000
        assert ev.pitch == 1000
        ev.pitch = -1000
        assert ev.pitch == -1000

    def test_set_tempo_event(self):
        ev = midi.SetTempoEvent()
        ev.bpm = 120
        assert abs(ev.bpm - 120.0) < 0.01
        assert ev.mpqn == 500000

    def test_time_signature_event(self):
        ev = midi.TimeSignatureEvent(data=[4, 2, 24, 8])
        assert ev.numerator == 4
        assert ev.denominator == 4
        assert ev.metronome == 24
        assert ev.thirtyseconds == 8

    def test_key_signature_event(self):
        ev = midi.KeySignatureEvent(data=[0, 0])
        assert ev.alternatives == 0
        assert ev.minor == 0

    def test_event_sorting(self):
        ev1 = midi.NoteOnEvent(tick=100)
        ev2 = midi.NoteOnEvent(tick=50)
        ev3 = midi.NoteOnEvent(tick=200)
        events = [ev1, ev2, ev3]
        events.sort()
        assert events[0].tick == 50
        assert events[1].tick == 100
        assert events[2].tick == 200

    def test_event_equality(self):
        ev1 = midi.NoteOnEvent(tick=100, channel=0, data=[60, 100])
        ev2 = midi.NoteOnEvent(tick=100, channel=0, data=[60, 100])
        assert ev1 == ev2

    def test_event_copy(self):
        ev = midi.NoteOnEvent(tick=100, channel=1, data=[60, 100])
        ev2 = ev.copy(tick=200)
        assert ev2.tick == 200
        assert ev2.channel == 1
        assert ev2.data == [60, 100]

    def test_text_meta_event(self):
        ev = midi.TextMetaEvent(data=[72, 101, 108, 108, 111])
        assert ev.text == "Hello"

    def test_unknown_meta_event(self):
        ev = midi.UnknownMetaEvent(metacommand=0x99, data=[1, 2, 3])
        assert ev.metacommand == 0x99
        assert ev.data == [1, 2, 3]

    def test_event_registry(self):
        assert 0x90 in midi.EventRegistry.Events  # NoteOn
        assert 0x80 in midi.EventRegistry.Events  # NoteOff
        assert 0x2F in midi.EventRegistry.MetaEvents  # EndOfTrack
        assert 0x51 in midi.EventRegistry.MetaEvents  # SetTempo
