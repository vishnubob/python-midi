#!/usr/bin/env python

import sys
import time
import midi
import midi.sequencer as sequencer

if len(sys.argv) != 3:
    print "Usage: {0} <client> <port>".format(sys.argv[0])
    #print "Usage: {0} <input client> <input port> <output client> <output port>".format(sys.argv[0])
    exit(2)

r_client = sys.argv[1]
r_port   = sys.argv[2]

#w_client= sys.argv[3]
#w_port  = sys.argv[4]

class Channel(object):
    __slots__ = ['_input', '_output']

    def __init__(self, input, output):
        self._input = input
        self._output = output

    def receiv(self):
        return self._input.event_read()

    def send(self, event):
        self._output.event_write(event, False, False, True)

class MultiChannelReader(object):
    # _sender is the last input to produce an event
    __slots__ = ['_inputs', '_sender']

    def __init__(self, inputs):
        self._inputs = inputs

    def receiv(self):
        for s in self._inputs:
            event = s.receiv()
            if event is not None:
                self._sender = s
                return event

class MidiActor(MultiChannelReader):
    def act(self):
        kill_bit = False
        while not kill_bit:
            event = self.receiv()
            if event is not None:
                self.handle(event)

    def reply(self, event):
        _sender.send(event)

    def handle(self, event):
       print "Implement me!" 
 
class PingPong(MidiActor):
    def handle(self, event):
        print event
        reply(event)

class EchoMaster(MidiActor):
    def handle(self, event):
        print event

writer = None
#writer = sequencer.SequencerWrite(sequencer_resolution=resolution)
#writer.subscribe_port(w_client, w_port)
#writer.start_sequencer()

reader = sequencer.SequencerRead(sequencer_resolution=120)
reader.subscribe_port(r_client, r_port)
reader.start_sequencer()

m = EchoMaster([Channel(reader, writer)])

m.act()
