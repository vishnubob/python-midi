#!/usr/bin/env python
"""Print a description of available MIDI hardware."""
import midi.sequencer as sequencer


def main() -> None:
    s = sequencer.SequencerHardware()
    print(s)


if __name__ == '__main__':
    main()
