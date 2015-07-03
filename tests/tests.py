import unittest
import midi
import mary_test
import note_match_test

class TestMIDI(unittest.TestCase):
    def test_varlen(self): 
        maxval = 0x0FFFFFFF
        for inval in xrange(0, maxval, maxval / 1000):
            datum = midi.write_varlen(inval)
            outval = midi.read_varlen(iter(datum))
            self.assertEqual(inval, outval)

    def test_mary(self): 
        midi.write_midifile("mary.mid", mary_test.MARY_MIDI)
        pattern1 = midi.read_midifile("mary.mid")
        midi.write_midifile("mary.mid", pattern1)
        pattern2 = midi.read_midifile("mary.mid")
        self.assertEqual(len(pattern1), len(pattern2))
        for track_idx in range(len(pattern1)):
            self.assertEqual(len(pattern1[track_idx]), len(pattern2[track_idx]))
            for event_idx in range(len(pattern1[track_idx])):
                event1 = pattern1[track_idx][event_idx]
                event2 = pattern2[track_idx][event_idx]
                self.assertEqual(event1.tick, event2.tick)
                self.assertEqual(event1.data, event2.data)

    def test_find_matching_note_off(self):

        pattern = note_match_test.standard_track()
        pattern.make_ticks_abs()
        print pattern 

        # general assertions about the pattern
        self.assertEqual(len(pattern), 1)
        track = pattern[0]
        self.assertEqual(len(track), 9)

        # find matching NoteOff event for first NoteOn event at tick=0
        # and make sure it's correct
        noteOnEventTick0 = track[0]
        self.assertEqual(noteOnEventTick0.pitch, midi.G_3)
        matchingNoteOffEvent = midi.find_matching_note_off(track, noteOnEventTick0)
        self.assertEqual(matchingNoteOffEvent.pitch, midi.G_3)
        self.assertEqual(matchingNoteOffEvent.tick, 160)

        # try passing a "NoteOffEvent", and make sure it returns None
        shouldBeNone = midi.find_matching_note_off(track, matchingNoteOffEvent)
        if shouldBeNone is not None:
            raise Exception("find_matching_note_off should have returned None")

        # find matching NoteOff event for second NoteOn event at tick=10
        # and make sure it's correct
        noteOnEventTick10 = track[1]
        matchingNoteOffEvent = midi.find_matching_note_off(track, noteOnEventTick10)
        self.assertEqual(matchingNoteOffEvent.pitch, midi.C_3)
        self.assertEqual(matchingNoteOffEvent.tick, 60)

        # try passing a "NoteOffEvent", and make sure it returns None
        shouldBeNone = midi.find_matching_note_off(track, matchingNoteOffEvent)
        if shouldBeNone is not None:
            raise Exception("find_matching_note_off should have returned None")

        # find matching NoteOff event for fourth NoteOn event
        # and make sure it's correct
        noteOnEventFourth = track[6]
        matchingNoteOffEvent = midi.find_matching_note_off(track, noteOnEventFourth)
        self.assertEqual(matchingNoteOffEvent.tick, 310)

 
if __name__ == '__main__':
    unittest.main()
