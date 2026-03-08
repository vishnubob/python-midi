Events
======

.. automodule:: midi.events
   :no-members:

.. inheritance-diagram:: midi.events
   :parts: 1

Base Classes
------------

.. autoclass:: midi.AbstractEvent
   :members:
   :special-members: __init__

.. autoclass:: midi.Event
   :members:
   :special-members: __init__

.. autoclass:: midi.MetaEvent
   :members:
   :special-members: __init__

.. autoclass:: midi.MetaEventWithText
   :members:
   :special-members: __init__

.. autoclass:: midi.NoteEvent
   :members:
   :special-members: __init__

Note Events
-----------

.. autoclass:: midi.NoteOnEvent
.. autoclass:: midi.NoteOffEvent

Channel Events
--------------

.. autoclass:: midi.AfterTouchEvent
   :members:
.. autoclass:: midi.ControlChangeEvent
   :members:
.. autoclass:: midi.ProgramChangeEvent
   :members:
.. autoclass:: midi.ChannelAfterTouchEvent
   :members:
.. autoclass:: midi.PitchWheelEvent
   :members:
.. autoclass:: midi.SysexEvent
   :members:

System Real-Time Events
-----------------------

.. autoclass:: midi.SystemRealTimeEvent
.. autoclass:: midi.ClockEvent
.. autoclass:: midi.StartEvent
.. autoclass:: midi.ContinueEvent
.. autoclass:: midi.StopEvent
.. autoclass:: midi.SongPositionPointerEvent
   :members:

Tempo and Time
--------------

.. autoclass:: midi.SetTempoEvent
   :members:
.. autoclass:: midi.TimeSignatureEvent
   :members:
.. autoclass:: midi.KeySignatureEvent
   :members:

Track Metadata
--------------

.. autoclass:: midi.TrackNameEvent
.. autoclass:: midi.InstrumentNameEvent
.. autoclass:: midi.EndOfTrackEvent

Text Events
-----------

.. autoclass:: midi.TextMetaEvent
.. autoclass:: midi.CopyrightMetaEvent
.. autoclass:: midi.LyricsEvent
.. autoclass:: midi.MarkerEvent
.. autoclass:: midi.CuePointEvent
.. autoclass:: midi.ProgramNameEvent

Other Meta Events
-----------------

.. autoclass:: midi.SequenceNumberMetaEvent
.. autoclass:: midi.ChannelPrefixEvent
.. autoclass:: midi.PortEvent
.. autoclass:: midi.TrackLoopEvent
.. autoclass:: midi.SmpteOffsetEvent
.. autoclass:: midi.SequencerSpecificEvent
.. autoclass:: midi.UnknownMetaEvent
