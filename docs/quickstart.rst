Quick Start
===========

Installation
------------

Requires Python 3.10+::

    pip install .

Building a MIDI File from Scratch
----------------------------------

.. code-block:: python

    import midi

    # Create a pattern (top-level container) with a single track
    pattern = midi.Pattern()
    track = midi.Track()
    pattern.append(track)

    # Add a note
    on = midi.NoteOnEvent(tick=0, velocity=20, pitch=midi.G_3)
    track.append(on)
    off = midi.NoteOffEvent(tick=100, pitch=midi.G_3)
    track.append(off)

    # Every track must end with EndOfTrackEvent
    eot = midi.EndOfTrackEvent(tick=1)
    track.append(eot)

    # Write to disk
    midi.write_midifile("example.mid", pattern)

Reading a MIDI File
-------------------

.. code-block:: python

    import midi

    pattern = midi.read_midifile("example.mid")
    print(pattern)
