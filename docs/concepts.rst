MIDI Concepts
=============

Ticks and Time
--------------

A tick represents the lowest-level resolution of a MIDI track.  MIDI files
use *relative* (delta) ticks by default — each event's tick is the offset
from the previous event, not an absolute time.

To convert between relative and absolute ticks, use
:meth:`~midi.Track.make_ticks_abs` and :meth:`~midi.Track.make_ticks_rel`.

Resolution and Tempo
--------------------

Two values determine how ticks map to wall-clock time:

- **Resolution** (PPQ): Pulses Per Quarter note.  Set once per file in
  :attr:`~midi.Pattern.resolution`.  Typically 220 or 480.
- **Tempo**: Beats Per Minute.  Set via :class:`~midi.SetTempoEvent`.
  Internally stored as *microseconds per quarter note* (MPQN).

The conversion::

    # 120 BPM → 500,000 µs per beat
    mpqn = 60_000_000 / bpm

    # With resolution=1000, one tick = 500 µs = 0.5 ms
    tick_us = mpqn / resolution

Time Signatures
---------------

:class:`~midi.TimeSignatureEvent` encodes the time signature (e.g. 4/4,
3/4, 6/8).  Time signatures affect notation but do **not** change the
tempo.
