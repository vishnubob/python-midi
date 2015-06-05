#!/usr/bin/env python
"""
Print a description of a MIDI file.
"""
import midi
import sys

if len(sys.argv) != 2:
    print("Usage: {0} <midifile>".format(sys.argv[0]))
    sys.exit(2)

midifile = sys.argv[1]
pattern = midi.read_midifile(midifile)
print(repr(pattern))
