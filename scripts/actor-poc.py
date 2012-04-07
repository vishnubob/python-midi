#!/usr/bin/env python

import sys
import time
import midi
import midi.sequencer as sequencer


def main():
    if len(sys.argv) != 3:
        print "Usage: {0} <music client:port> <node client:port>".format(sys.argv[0])
        exit(2)

    args = sys.argv

    music_client, music_port = args[1].split(":")
    node_client,  node_port  = args[2].split(":")
    
    synth = Channel(None, start_writer(music_client, music_port))
    picture_box = Channel(start_reader(node_client, node_port), None)
    
    server = Server(synth, [picture_box])
    server.act()

class Channel(object):

    def __init__(self, input, output):
        self._input = input
        self._output = output

    def receiv(self):
        return self._input.event_read()

    def send(self, event):
        self._output.event_write(event, False, False, True)

class MidiActor(object):
    __slots__ = ['_channels', '_sender']

    def __init__(self, channels):
        self._channels = channels

    def act(self):
        while True:
            event = self.receiv()
            if event is not None:
                self.handle(event)

    def receiv(self):
        for s in self._channels:
            event = s.receiv()
            if event is not None:
                self._sender = s
                return event

    def reply(self, event):
        self._sender.send(event)

    def handle(self, event):
        print "Implement me!" 

class EchoMaster(MidiActor):
    def handle(self, event):
       print event

class Server(MidiActor):
    __slots__ = ['synth'] 

    def __init__(self, synth, picture_boxes):
        super(Server, self).__init__(picture_boxes)
        self.synth = synth

    def handle(self, event):
        print "forwarding " + repr(event)
        self.synth.send(event)

def start_reader(client, port):
    seq = sequencer.SequencerRead(sequencer_resolution=120)
    seq.subscribe_port(client, port)
    seq.start_sequencer()
    return seq

def start_writer(client, port):
    seq = sequencer.SequencerWrite(sequencer_resolution=120)
    seq.subscribe_port(client, port)
    seq.start_sequencer()
    return seq

if __name__ == '__main__':
    main()
