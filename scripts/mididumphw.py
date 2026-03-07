#!/usr/bin/env python
"""
Print available MIDI devices with source and destination endpoint refs.

Use the source refs for recording (midirecord.py) and dest refs for
playback (midiplay.py).
"""
import midi.sequencer as sequencer

s = sequencer.SequencerHardware()

print(s)
