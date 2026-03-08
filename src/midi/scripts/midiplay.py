#!/usr/bin/env python
"""Attach to a MIDI device and send the contents of a MIDI file to it."""
import sys
import time
import midi
import midi.sequencer as sequencer


def main() -> None:
    if len(sys.argv) != 4:
        print(f"Usage: {sys.argv[0]} <client> <port> <file>")
        sys.exit(2)

    client = sys.argv[1]
    port = sys.argv[2]
    filename = sys.argv[3]

    pattern = midi.read_midifile(filename)

    hardware = sequencer.SequencerHardware()

    try:
        client_id, port_id = hardware.get_client_and_port(client, port)
    except KeyError:
        if client.isdigit() and port.isdigit():
            client_id, port_id = int(client), int(port)
        else:
            print(f"Device not found: {client} / {port}")
            sys.exit(1)

    seq = sequencer.SequencerWrite(sequencer_resolution=pattern.resolution)
    seq.subscribe_port(client_id, port_id)

    pattern.make_ticks_abs()
    events = []
    for track in pattern:
        for event in track:
            events.append(event)
    events.sort()
    seq.start_sequencer()
    for event in events:
        buf = seq.event_write(event, False, False, True)
        if buf is None:
            continue
        if buf < 1000:
            time.sleep(.5)
    while event.tick > seq.queue_get_tick_time():
        seq.drain()
        time.sleep(.5)

    print('The end?')


if __name__ == '__main__':
    main()
