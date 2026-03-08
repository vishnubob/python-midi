#!/usr/bin/env python
"""
Record MIDI input from a source endpoint and write to a MIDI file.

Usage: midirecord <source> <output.mid> [duration_seconds]

<source> can be a device name or numeric endpoint ref.
Use mididumphw to find available devices.
Press Ctrl-C to stop recording (or wait for the optional duration).
"""
import signal
import sys
import time

import midi
import midi.sequencer as sequencer


def _resolve_source(source_arg: str) -> tuple[int, int]:
    """Resolve source argument to (client_id, port_id).

    Tries name-based lookup first, then falls back to numeric endpoint ref.
    """
    hardware = sequencer.SequencerHardware()
    # Try name-based: match any client that contains the source_arg,
    # pick the first readable port
    for client in hardware:
        if client.name == source_arg:
            for port in client:
                if getattr(port, 'caps_read', False) or getattr(port, 'source_ref', None) is not None:
                    return (client.client, port.port)
    # Fallback to numeric
    if source_arg.isdigit():
        return (0, int(source_arg))
    print(f"Source not found: {source_arg}")
    sys.exit(1)


def main():
    if len(sys.argv) < 3 or len(sys.argv) > 4:
        print("Usage: %s <source> <output.mid> [duration_seconds]"
              % sys.argv[0])
        sys.exit(2)

    source_arg = sys.argv[1]
    output_file = sys.argv[2]
    duration = float(sys.argv[3]) if len(sys.argv) == 4 else None

    client_id, port_id = _resolve_source(source_arg)

    resolution = 480
    seq = sequencer.SequencerRead(sequencer_resolution=resolution)
    seq.subscribe_port(client_id, port_id)

    events = []
    stop = False

    def handle_sigint(signum, frame):
        nonlocal stop
        stop = True

    signal.signal(signal.SIGINT, handle_sigint)

    print("Recording from %s to %s ..." % (source_arg, output_file))
    if duration:
        print("Will stop after %.1f seconds. Press Ctrl-C to stop early." % duration)
    else:
        print("Press Ctrl-C to stop.")

    seq.start_sequencer()
    start_time = time.time()

    while not stop:
        ev = seq.event_read()
        if ev is not None:
            events.append(ev)
            print("  %s" % ev)
        else:
            time.sleep(0.001)
        if duration and (time.time() - start_time) >= duration:
            break

    seq.stop_sequencer()
    print("\nRecording stopped. Captured %d events." % len(events))

    if not events:
        print("No events recorded, not writing file.")
        return

    # Sort by tick (absolute) and convert to relative deltas
    events.sort(key=lambda e: e.tick)
    track = midi.Track()
    prev_tick = 0
    for ev in events:
        ev.tick = ev.tick - prev_tick
        prev_tick += ev.tick
        track.append(ev)
    track.append(midi.EndOfTrackEvent(tick=0))

    pattern = midi.Pattern(resolution=resolution)
    pattern.append(track)

    midi.write_midifile(output_file, pattern)
    print("Written to %s" % output_file)


if __name__ == '__main__':
    main()
