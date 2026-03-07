import sys
import pytest

import midi


@pytest.mark.skipif(sys.platform != 'darwin', reason="CoreMIDI only on macOS")
class TestCoreMIDISequencer:
    def test_import(self):
        import midi.sequencer as sequencer
        assert hasattr(sequencer, 'Sequencer')
        assert sequencer.Sequencer.SEQUENCER_TYPE == 'coremidi'

    def test_hardware_enumeration(self):
        import midi.sequencer as sequencer
        hw = sequencer.SequencerHardware()
        # Should enumerate without error
        assert isinstance(len(hw), int)

    def test_sequencer_write_create(self):
        import midi.sequencer as sequencer
        seq = sequencer.SequencerWrite(sequencer_resolution=1000)
        assert seq.sequencer_resolution == 1000

    def test_sequencer_read_create(self):
        import midi.sequencer as sequencer
        seq = sequencer.SequencerRead(sequencer_resolution=1000)
        assert seq.sequencer_resolution == 1000

    def test_tick_timing(self):
        import midi.sequencer as sequencer
        seq = sequencer.SequencerWrite(
            sequencer_tempo=120, sequencer_resolution=1000)
        seq.start_sequencer()
        tick = seq.queue_get_tick_time()
        assert isinstance(tick, int)
        seq.stop_sequencer()


@pytest.mark.skipif(sys.platform != 'linux', reason="ALSA only on Linux")
class TestALSASequencer:
    def test_import(self):
        import midi.sequencer as sequencer
        assert hasattr(sequencer, 'Sequencer')
        assert sequencer.Sequencer.SEQUENCER_TYPE == 'alsa'
