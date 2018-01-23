#!/usr/bin/env python
"""
Print a description of the available devices.
"""
from __future__ import print_function
import midi.sequencer as sequencer

s = sequencer.SequencerHardware()

print(s)
