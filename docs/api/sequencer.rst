Sequencer
=========

The sequencer backend is selected automatically based on your platform:

- **Linux**: ALSA sequencer via SWIG wrapper
- **macOS**: CoreMIDI sequencer via pure ctypes

.. note::

   Sequencer classes are only available on their respective platforms.
   Import ``midi.sequencer`` to get the platform-appropriate backend.

The sequencer API provides three main classes:

- ``SequencerHardware`` — enumerate MIDI devices
- ``SequencerWrite`` — send MIDI events to a device
- ``SequencerRead`` — receive MIDI events from a device
