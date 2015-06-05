#!/usr/bin/env python
"""
Attach to a MIDI device and print events to standard output.
"""
import sys
import time
import midi
import midi.sequencer as sequencer

if len(sys.argv) != 3:
    print("Usage: {0} <client> <port>".format(sys.argv[0]))
    exit(2)

client = sys.argv[1]
port   = sys.argv[2]

seq = sequencer.SequencerRead(sequencer_resolution=120)
seq.subscribe_port(client, port)
seq.start_sequencer()

while True:
  event = seq.event_read()
  if event is not None:
      print(event)
