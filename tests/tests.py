import unittest
import midi
import mary_test

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

if __name__ == '__main__':
    unittest.main()
