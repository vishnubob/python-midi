#!/usr/bin/env python
"""
Attach to a MIDI device and print events to standard output.
"""
import sys
import time

import midi
import midi.sequencer as sequencer


def main():
    if len(sys.argv) != 3:
        print(f"Usage: {sys.argv[0]} <client> <port>")
        sys.exit(2)

    client = sys.argv[1]
    port = sys.argv[2]

    hardware = sequencer.SequencerHardware()

    try:
        client_id, port_id = hardware.get_client_and_port(client, port)
    except KeyError:
        if client.isdigit() and port.isdigit():
            client_id, port_id = int(client), int(port)
        else:
            print(f"Device not found: {client} / {port}")
            sys.exit(1)

    seq = sequencer.SequencerRead(sequencer_resolution=120)
    seq.subscribe_port(client_id, port_id)
    seq.start_sequencer()

    while True:
        event = seq.event_read()
        if event is not None:
            print(event)


if __name__ == '__main__':
    main()
