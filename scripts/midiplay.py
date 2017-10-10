#!/usr/bin/env python
"""
Attach to a MIDI device and send the contents of a MIDI file to it.
"""
from __future__ import print_function

import sys
import time
import midi
import midi.sequencer as sequencer

if len(sys.argv) != 4:
    print("Usage: {0} <client> <port> <file>".format(sys.argv[0]))
    exit(2)

client   = sys.argv[1]
port     = sys.argv[2]
filename = sys.argv[3]

pattern = midi.read_midifile(filename)

hardware = sequencer.SequencerHardware()

if not client.isdigit:
    client = hardware.get_client(client)

if not port.isdigit:
    port = hardware.get_port(port)    

seq = sequencer.SequencerWrite(sequencer_resolution=pattern.resolution)
seq.subscribe_port(client, port)

pattern.make_ticks_abs()
events = []
for track in pattern:
    for event in track:
        events.append(event)
events.sort()
seq.start_sequencer()
for event in events:
    buf = seq.event_write(event, False, False, True)
    if buf == None:
        continue
    if buf < 1000:
        time.sleep(.5)
while event.tick > seq.queue_get_tick_time():
    seq.drain()
    time.sleep(.5)

print('The end?')
