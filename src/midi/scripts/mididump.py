#!/usr/bin/env python
"""Print a description of a MIDI file."""
import sys
import midi


def main() -> None:
    if len(sys.argv) != 2:
        print(f"Usage: {sys.argv[0]} <midifile>")
        sys.exit(2)
    midifile = sys.argv[1]
    pattern = midi.read_midifile(midifile)
    print(repr(pattern))


if __name__ == '__main__':
    main()
