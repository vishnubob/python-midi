#!/usr/bin/env python
"""
Record MIDI input from a source endpoint and write to a MIDI file.

Usage: midirecord.py <source_endpoint_ref> <output.mid> [duration_seconds]

Use mididumphw.py to find source endpoint refs.
Press Ctrl-C to stop recording (or wait for the optional duration).
"""
import signal
import sys
import time

import midi
import midi.sequencer as sequencer


def main():
    if len(sys.argv) < 3 or len(sys.argv) > 4:
        print("Usage: %s <source_endpoint_ref> <output.mid> [duration_seconds]"
              % sys.argv[0])
        sys.exit(2)

    source_ref = int(sys.argv[1])
    output_file = sys.argv[2]
    duration = float(sys.argv[3]) if len(sys.argv) == 4 else None

    resolution = 480
    seq = sequencer.SequencerRead(sequencer_resolution=resolution)
    seq.subscribe_port(0, source_ref)

    events = []
    stop = False

    def handle_sigint(signum, frame):
        nonlocal stop
        stop = True

    signal.signal(signal.SIGINT, handle_sigint)

    print("Recording from source %d to %s ..." % (source_ref, output_file))
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
