python-midi
===========

Python, for all its amazing ability out of the box, does not provide you with
an easy means to manipulate MIDI data.  This toolkit fills that gap with a
high-level framework that is independent of hardware.  It offers a reasonable
object granularity to make MIDI streams painless to manipulate, sequence,
record, and playback.

Features
--------

- High level class types that represent individual MIDI events.
- A multi-track aware container for managing MIDI events.
- A reader and writer for Standard MIDI Files.
- Real-time sequencer support (ALSA on Linux, CoreMIDI on macOS).

.. toctree::
   :maxdepth: 2
   :caption: Contents

   quickstart
   concepts
   api/index
   cli
