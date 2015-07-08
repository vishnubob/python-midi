import unittest
import midi
import mary_test
import time
import os

try:
    import midi.sequencer as sequencer
except ImportError:
    sequencer = None

def get_sequencer_type():
    if sequencer == None:
        return None
    return sequencer.Sequencer.SEQUENCER_TYPE

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

class TestSequencerALSA(unittest.TestCase):
    TEMPO = 120
    RESOLUTION = 1000

    def get_loop_client_port(self):
        hw = sequencer.SequencerHardware()
        ports = {port.name: port for port in hw}
        loop = ports.get("Midi Through", None)
        assert loop != None, "Could not find Midi Through port!"
        loop_port = loop.get_port("Midi Through Port-0")
        return (loop.client, loop_port.port)
    
    def get_reader_sequencer(self):
        (client, port) = self.get_loop_client_port()
        seq = sequencer.SequencerRead(sequencer_resolution=self.RESOLUTION)
        seq.subscribe_port(client, port)
        return seq

    def get_writer_sequencer(self):
        (client, port) = self.get_loop_client_port()
        seq = sequencer.SequencerWrite(sequencer_resolution=self.RESOLUTION)
        seq.subscribe_port(client, port)
        return seq
    
    @unittest.skipIf(get_sequencer_type() != "alsa", "ALSA Sequencer not found, skipping test")
    @unittest.skipIf(not os.path.exists("/dev/snd/seq"), "/dev/snd/seq is not available, skipping test")
    def test_loopback_sequencer(self):
        rseq = self.get_reader_sequencer()
        wseq = self.get_writer_sequencer()
        start_time = time.time()
        delay = 0.6
        rseq.start_sequencer()
        wseq.start_sequencer()
        tick = int((self.TEMPO / 60.0) * self.RESOLUTION * delay)
        send_event = midi.NoteOnEvent(tick=tick, velocity=20, pitch=midi.G_3)
        wseq.event_write(send_event, False, False, True)
        recv_event = rseq.event_read()
        while 1:
            now = time.time()
            recv_event = rseq.event_read()
            if recv_event is not None:
                break
            if (now - start_time) > (2 * delay):
                break
            time.sleep(.01)
        delta = now - start_time
        # make sure we received this event at the proper time
        self.assertGreaterEqual(delta, delay)
        # make sure this event is the one we transmitted
        self.assertEqual(send_event.data, recv_event.data)
        self.assertEqual(send_event.__class__, recv_event.__class__)

if __name__ == '__main__':
    unittest.main()
