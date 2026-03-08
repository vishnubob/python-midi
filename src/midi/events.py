"""MIDI event types — channel messages, meta events, and system messages.

All event classes inherit from :class:`AbstractEvent` and are automatically
registered in :class:`EventRegistry` via ``__init_subclass__``.
"""
from __future__ import annotations

import math
import functools


class EventRegistry:
    Events: dict[int, type[Event]] = {}
    MetaEvents: dict[int, type[MetaEvent]] = {}

    @classmethod
    def register_event(cls, event: type[AbstractEvent], bases: tuple[type, ...]) -> None:
        if (Event in bases) or (NoteEvent in bases):
            assert event.statusmsg not in cls.Events, \
                            "Event %s already registered" % event.name
            cls.Events[event.statusmsg] = event
        elif (MetaEvent in bases) or (MetaEventWithText in bases):
            mc = event.__dict__.get('metacommand', getattr(event, 'metacommand', None))
            if isinstance(mc, int):
                assert mc not in cls.MetaEvents, \
                                "Event %s already registered" % event.name
                cls.MetaEvents[mc] = event
        else:
            raise ValueError("Unknown bases class in event type: " + event.name)


@functools.total_ordering
class AbstractEvent:
    """Base class for all MIDI events.

    Every event has a ``tick`` (timing), a ``data`` property, and is
    orderable by tick.  Construct events using keyword arguments::

        NoteOnEvent(tick=0, pitch=60, velocity=100, channel=0)

    Attributes:
        tick: Tick offset — relative (delta) or absolute depending on
            the containing Track.
        data: Event payload as a tuple of ints.  Subclasses provide
            typed properties (e.g. ``pitch``, ``velocity``) that
            read/write the underlying data.
    """
    __slots__ = ('tick', 'msdelay')
    name: str = "Generic MIDI Event"
    length: int = 0
    statusmsg: int = 0x0

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls.__name__ not in ('Event', 'MetaEvent', 'NoteEvent',
                                'MetaEventWithText',
                                'SystemRealTimeEvent',
                                'SongPositionPointerEvent'):
            EventRegistry.register_event(cls, cls.__mro__)

    def __init__(self, **kw: object) -> None:
        self.tick: int = 0
        self.msdelay: float = 0.0
        if 'data' in kw:
            self.data = kw.pop('data')
        for key in kw:
            try:
                setattr(self, key, kw[key])
            except AttributeError:
                pass

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, AbstractEvent):
            return NotImplemented
        return self.tick == other.tick and self.data == other.data

    def __lt__(self, other: object) -> bool:
        if not isinstance(other, AbstractEvent):
            return NotImplemented
        if self.tick != other.tick:
            return self.tick < other.tick
        return self.data < other.data

    def __hash__(self) -> int:
        return id(self)

    def __baserepr__(self, keys: list[str] | None = None) -> str:
        if keys is None:
            keys = []
        keys = ['tick'] + keys + ['data']
        body = []
        for key in keys:
            val = getattr(self, key)
            keyval = "%s=%r" % (key, val)
            body.append(keyval)
        body_str = ', '.join(body)
        return "midi.%s(%s)" % (self.__class__.__name__, body_str)

    def __repr__(self) -> str:
        return self.__baserepr__()


@functools.total_ordering
class Event(AbstractEvent):
    """Base class for MIDI channel messages (status ``0x80``--``0xEF``).

    Attributes:
        channel: MIDI channel (0--15).
    """
    __slots__ = ('channel',)
    name: str = 'Event'
    channel: int

    def __init__(self, **kw: object) -> None:
        if 'channel' not in kw:
            kw = kw.copy()
            kw['channel'] = 0
        super().__init__(**kw)

    def copy(self, **kw: object) -> Event:
        _kw: dict[str, object] = {'channel': self.channel, 'tick': self.tick, 'data': list(self.data)}
        _kw.update(kw)
        return self.__class__(**_kw)

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, AbstractEvent):
            return NotImplemented
        return self.tick == other.tick

    def __lt__(self, other: object) -> bool:
        if not isinstance(other, AbstractEvent):
            return NotImplemented
        return self.tick < other.tick

    def __hash__(self) -> int:
        return id(self)

    def __repr__(self) -> str:
        return self.__baserepr__(['channel'])

    @classmethod
    def is_event(cls, statusmsg: int) -> bool:
        return (cls.statusmsg == (statusmsg & 0xF0))


class MetaEvent(AbstractEvent):
    """Base class for MIDI meta events (status ``0xFF``).

    Meta events carry non-performance data such as tempo, time
    signature, track names, and lyrics.  Each subclass has a unique
    ``metacommand`` byte.
    """
    __slots__ = ('_data',)
    statusmsg: int = 0xFF
    metacommand: int = 0x0
    name: str = 'Meta Event'

    def __init__(self, **kw: object) -> None:
        self._data: list[int] = []
        super().__init__(**kw)

    @property
    def data(self) -> tuple[int, ...]:
        return tuple(self._data)

    @data.setter
    def data(self, value) -> None:
        self._data = list(value)

    def copy(self, **kw: object) -> MetaEvent:
        _kw: dict[str, object] = {'tick': self.tick, 'data': list(self.data)}
        _kw.update(kw)
        return self.__class__(**_kw)

    @classmethod
    def is_event(cls, statusmsg: int) -> bool:
        return (statusmsg == 0xFF)


class NoteEvent(Event):
    """Base class for note-on and note-off events.

    Attributes:
        pitch: MIDI note number (0--127).
        velocity: Key velocity (0--127).
    """
    __slots__ = ('_pitch', '_velocity')
    length: int = 2

    def __init__(self, **kw: object) -> None:
        self._pitch: int = 0
        self._velocity: int = 0
        super().__init__(**kw)

    @property
    def pitch(self) -> int: return self._pitch
    @pitch.setter
    def pitch(self, val: int) -> None: self._pitch = val

    @property
    def velocity(self) -> int: return self._velocity
    @velocity.setter
    def velocity(self, val: int) -> None: self._velocity = val

    @property
    def data(self) -> tuple[int, ...]:
        return (self._pitch, self._velocity)

    @data.setter
    def data(self, value) -> None:
        self._pitch = value[0] if len(value) > 0 else 0
        self._velocity = value[1] if len(value) > 1 else 0


class NoteOnEvent(NoteEvent):
    """Note On message (status ``0x90``).

    A velocity of 0 is equivalent to a :class:`NoteOffEvent`.
    """
    __slots__ = ()
    statusmsg: int = 0x90
    name: str = 'Note On'

class NoteOffEvent(NoteEvent):
    """Note Off message (status ``0x80``)."""
    __slots__ = ()
    statusmsg: int = 0x80
    name: str = 'Note Off'

class AfterTouchEvent(Event):
    """Polyphonic aftertouch / key pressure (status ``0xA0``).

    Attributes:
        pitch: Note number (0--127).
        value: Pressure value (0--127).
    """
    __slots__ = ('_pitch', '_value')
    statusmsg: int = 0xA0
    length: int = 2
    name: str = 'After Touch'

    def __init__(self, **kw: object) -> None:
        self._pitch: int = 0
        self._value: int = 0
        super().__init__(**kw)

    @property
    def pitch(self) -> int: return self._pitch
    @pitch.setter
    def pitch(self, val: int) -> None: self._pitch = val

    @property
    def value(self) -> int: return self._value
    @value.setter
    def value(self, val: int) -> None: self._value = val

    @property
    def data(self) -> tuple[int, ...]:
        return (self._pitch, self._value)

    @data.setter
    def data(self, value) -> None:
        self._pitch = value[0] if len(value) > 0 else 0
        self._value = value[1] if len(value) > 1 else 0


class ControlChangeEvent(Event):
    """Control Change message (status ``0xB0``).

    Attributes:
        control: Controller number (0--127).
        value: Controller value (0--127).
    """
    __slots__ = ('_control', '_value')
    statusmsg: int = 0xB0
    length: int = 2
    name: str = 'Control Change'

    def __init__(self, **kw: object) -> None:
        self._control: int = 0
        self._value: int = 0
        super().__init__(**kw)

    @property
    def control(self) -> int: return self._control
    @control.setter
    def control(self, val: int) -> None: self._control = val

    @property
    def value(self) -> int: return self._value
    @value.setter
    def value(self, val: int) -> None: self._value = val

    @property
    def data(self) -> tuple[int, ...]:
        return (self._control, self._value)

    @data.setter
    def data(self, value) -> None:
        self._control = value[0] if len(value) > 0 else 0
        self._value = value[1] if len(value) > 1 else 0


class ProgramChangeEvent(Event):
    """Program Change message (status ``0xC0``).

    Attributes:
        value: Program number (0--127).
    """
    __slots__ = ('_value',)
    statusmsg: int = 0xC0
    length: int = 1
    name: str = 'Program Change'

    def __init__(self, **kw: object) -> None:
        self._value: int = 0
        super().__init__(**kw)

    @property
    def value(self) -> int: return self._value
    @value.setter
    def value(self, val: int) -> None: self._value = val

    @property
    def data(self) -> tuple[int, ...]:
        return (self._value,)

    @data.setter
    def data(self, value) -> None:
        self._value = value[0] if len(value) > 0 else 0


class ChannelAfterTouchEvent(Event):
    """Channel aftertouch / pressure (status ``0xD0``).

    Attributes:
        value: Pressure value (0--127).
    """
    __slots__ = ('_value',)
    statusmsg: int = 0xD0
    length: int = 1
    name: str = 'Channel After Touch'

    def __init__(self, **kw: object) -> None:
        self._value: int = 0
        super().__init__(**kw)

    @property
    def value(self) -> int: return self._value
    @value.setter
    def value(self, val: int) -> None: self._value = val

    @property
    def data(self) -> tuple[int, ...]:
        return (self._value,)

    @data.setter
    def data(self, value) -> None:
        self._value = value[0] if len(value) > 0 else 0


class PitchWheelEvent(Event):
    """Pitch Wheel Change message (status ``0xE0``).

    Attributes:
        pitch: Signed pitch bend value (-8192 to +8191).
            Encoded as a 14-bit value centered on ``0x2000``.
    """
    __slots__ = ('_pitch',)
    statusmsg: int = 0xE0
    length: int = 2
    name: str = 'Pitch Wheel'

    def __init__(self, **kw: object) -> None:
        self._pitch: int = 0
        super().__init__(**kw)

    @property
    def pitch(self) -> int: return self._pitch
    @pitch.setter
    def pitch(self, val: int) -> None: self._pitch = val

    @property
    def data(self) -> tuple[int, ...]:
        value = self._pitch + 0x2000
        return (value & 0x7F, (value >> 7) & 0x7F)

    @data.setter
    def data(self, value) -> None:
        if len(value) >= 2:
            self._pitch = ((value[1] << 7) | value[0]) - 0x2000


class SysexEvent(Event):
    """System Exclusive message (status ``0xF0``).

    Variable-length manufacturer-specific data.
    """
    __slots__ = ('_data',)
    statusmsg: int = 0xF0
    name: str = 'SysEx'
    length: int = -1

    def __init__(self, **kw: object) -> None:
        self._data: list[int] = []
        super().__init__(**kw)

    @property
    def data(self) -> tuple[int, ...]:
        return tuple(self._data)

    @data.setter
    def data(self, value) -> None:
        self._data = list(value)

    @classmethod
    def is_event(cls, statusmsg: int) -> bool:
        return (cls.statusmsg == statusmsg)


class SystemRealTimeEvent(AbstractEvent):
    """MIDI System Real-Time messages (single status byte, no data)."""
    __slots__ = ()
    length: int = 0

    def __init_subclass__(cls, **kwargs: object) -> None:
        super(AbstractEvent, cls).__init_subclass__(**kwargs)

    @property
    def data(self) -> tuple[int, ...]: return ()

    @data.setter
    def data(self, value) -> None: pass

class ClockEvent(SystemRealTimeEvent):
    """MIDI Clock pulse (status ``0xF8``).  24 per quarter note."""
    __slots__ = ()
    statusmsg: int = 0xF8
    name: str = 'Clock'

class StartEvent(SystemRealTimeEvent):
    """Start playback (status ``0xFA``)."""
    __slots__ = ()
    statusmsg: int = 0xFA
    name: str = 'Start'

class ContinueEvent(SystemRealTimeEvent):
    """Continue playback (status ``0xFB``)."""
    __slots__ = ()
    statusmsg: int = 0xFB
    name: str = 'Continue'

class StopEvent(SystemRealTimeEvent):
    """Stop playback (status ``0xFC``)."""
    __slots__ = ()
    statusmsg: int = 0xFC
    name: str = 'Stop'

class SongPositionPointerEvent(AbstractEvent):
    """Song Position Pointer (0xF2). Position in sixteenth notes."""
    __slots__ = ('_position',)
    statusmsg: int = 0xF2
    name: str = 'Song Position Pointer'
    length: int = 2

    def __init_subclass__(cls, **kwargs: object) -> None:
        super(AbstractEvent, cls).__init_subclass__(**kwargs)

    def __init__(self, **kw: object) -> None:
        self._position: int = 0
        super().__init__(**kw)

    @property
    def position(self) -> int: return self._position
    @position.setter
    def position(self, val: int) -> None: self._position = val

    @property
    def data(self) -> tuple[int, ...]:
        return (self._position & 0x7F, (self._position >> 7) & 0x7F)

    @data.setter
    def data(self, value) -> None:
        if len(value) >= 2:
            self._position = (value[1] << 7) | value[0]


class SequenceNumberMetaEvent(MetaEvent):
    """Sequence Number meta event (``0x00``)."""
    __slots__ = ()
    name: str = 'Sequence Number'
    metacommand: int = 0x00
    length: int = 2

class MetaEventWithText(MetaEvent):
    """Base class for text-bearing meta events.

    Attributes:
        text: The text content.  Automatically encoded/decoded from
            the raw ``data`` bytes.
    """
    __slots__ = ('text',)
    text: str

    def __init__(self, **kw: object) -> None:
        self.text: str = ''
        super().__init__(**kw)

    @property
    def data(self) -> tuple[int, ...]:
        return tuple(ord(c) for c in self.text)

    @data.setter
    def data(self, value) -> None:
        self.text = ''.join(chr(b) for b in value)

    def __repr__(self) -> str:
        return self.__baserepr__(['text'])

class TextMetaEvent(MetaEventWithText):
    """General text annotation (``0x01``)."""
    __slots__ = ()
    name: str = 'Text'
    metacommand: int = 0x01
    length: int = -1

class CopyrightMetaEvent(MetaEventWithText):
    """Copyright notice (``0x02``)."""
    __slots__ = ()
    name: str = 'Copyright Notice'
    metacommand: int = 0x02
    length: int = -1

class TrackNameEvent(MetaEventWithText):
    """Track or sequence name (``0x03``)."""
    __slots__ = ()
    name: str = 'Track Name'
    metacommand: int = 0x03
    length: int = -1

class InstrumentNameEvent(MetaEventWithText):
    """Instrument name (``0x04``)."""
    __slots__ = ()
    name: str = 'Instrument Name'
    metacommand: int = 0x04
    length: int = -1

class LyricsEvent(MetaEventWithText):
    """Lyrics text (``0x05``)."""
    __slots__ = ()
    name: str = 'Lyrics'
    metacommand: int = 0x05
    length: int = -1

class MarkerEvent(MetaEventWithText):
    """Marker / rehearsal point (``0x06``)."""
    __slots__ = ()
    name: str = 'Marker'
    metacommand: int = 0x06
    length: int = -1

class CuePointEvent(MetaEventWithText):
    """Cue point for synchronization (``0x07``)."""
    __slots__ = ()
    name: str = 'Cue Point'
    metacommand: int = 0x07
    length: int = -1

class ProgramNameEvent(MetaEventWithText):
    """Program / patch name (``0x08``)."""
    __slots__ = ()
    name: str = 'Program Name'
    metacommand: int = 0x08
    length: int = -1

class UnknownMetaEvent(MetaEvent):
    """Placeholder for unrecognized meta events."""
    __slots__ = ('_metacommand',)
    name: str = 'Unknown'
    metacommand: int | None = None

    def __init__(self, **kw: object) -> None:
        self._metacommand: int = kw.pop('metacommand')
        super().__init__(**kw)

    @property
    def metacommand(self) -> int:
        return self._metacommand

    @metacommand.setter
    def metacommand(self, val: int) -> None:
        self._metacommand = val

    def copy(self, **kw: object) -> UnknownMetaEvent:
        kw['metacommand'] = self.metacommand
        return super().copy(**kw)

class ChannelPrefixEvent(MetaEvent):
    """Channel Prefix meta event (``0x20``)."""
    __slots__ = ()
    name: str = 'Channel Prefix'
    metacommand: int = 0x20
    length: int = 1

class PortEvent(MetaEvent):
    """MIDI Port / Cable meta event (``0x21``)."""
    __slots__ = ()
    name: str = 'MIDI Port/Cable'
    metacommand: int = 0x21
    length: int = -1

class TrackLoopEvent(MetaEvent):
    """Track Loop meta event (``0x2E``)."""
    __slots__ = ()
    name: str = 'Track Loop'
    metacommand: int = 0x2E
    length: int = -1

class EndOfTrackEvent(MetaEvent):
    """End of Track marker (``0x2F``).  Required at the end of every track."""
    __slots__ = ()
    name: str = 'End of Track'
    metacommand: int = 0x2F

class SetTempoEvent(MetaEvent):
    """Set Tempo meta event (``0x51``).

    Attributes:
        bpm: Tempo in beats per minute (read/write convenience).
        mpqn: Microseconds per quarter note (the raw MIDI encoding).
    """
    __slots__ = ('_mpqn', 'mpt')
    name: str = 'Set Tempo'
    metacommand: int = 0x51
    length: int = 3

    def __init__(self, **kw: object) -> None:
        self._mpqn: int = 500000
        self.mpt: float = 0.0
        super().__init__(**kw)

    @property
    def data(self) -> tuple[int, ...]:
        return ((self._mpqn >> 16) & 0xFF,
                (self._mpqn >> 8) & 0xFF,
                self._mpqn & 0xFF)

    @data.setter
    def data(self, value) -> None:
        if len(value) >= 3:
            self._mpqn = (value[0] << 16) | (value[1] << 8) | value[2]

    @property
    def mpqn(self) -> int: return self._mpqn
    @mpqn.setter
    def mpqn(self, val: int) -> None: self._mpqn = val

    @property
    def bpm(self) -> float: return float(6e7) / self._mpqn
    @bpm.setter
    def bpm(self, bpm: float) -> None: self._mpqn = int(float(6e7) / bpm)

class SmpteOffsetEvent(MetaEvent):
    """SMPTE Offset meta event (``0x54``)."""
    __slots__ = ()
    name: str = 'SMPTE Offset'
    metacommand: int = 0x54
    length: int = -1

class TimeSignatureEvent(MetaEvent):
    """Time Signature meta event (``0x58``).

    Attributes:
        numerator: Beats per bar (e.g. 4 for 4/4 time).
        denominator: Beat unit as a note value (e.g. 4 = quarter note).
            Stored internally as a power of 2.
        metronome: MIDI clocks per metronome click.
        thirtyseconds: Number of 32nd notes per MIDI quarter note.
    """
    __slots__ = ('_numerator', '_denominator_power', '_metronome', '_thirtyseconds')
    name: str = 'Time Signature'
    metacommand: int = 0x58
    length: int = 4

    def __init__(self, **kw: object) -> None:
        self._numerator: int = 0
        self._denominator_power: int = 0
        self._metronome: int = 0
        self._thirtyseconds: int = 0
        super().__init__(**kw)

    @property
    def numerator(self) -> int: return self._numerator
    @numerator.setter
    def numerator(self, val: int) -> None: self._numerator = val

    @property
    def denominator(self) -> int: return 2 ** self._denominator_power
    @denominator.setter
    def denominator(self, val: int) -> None: self._denominator_power = int(math.log(val, 2))

    @property
    def metronome(self) -> int: return self._metronome
    @metronome.setter
    def metronome(self, val: int) -> None: self._metronome = val

    @property
    def thirtyseconds(self) -> int: return self._thirtyseconds
    @thirtyseconds.setter
    def thirtyseconds(self, val: int) -> None: self._thirtyseconds = val

    @property
    def data(self) -> tuple[int, ...]:
        return (self._numerator, self._denominator_power, self._metronome, self._thirtyseconds)

    @data.setter
    def data(self, value) -> None:
        if len(value) >= 4:
            self._numerator = value[0]
            self._denominator_power = value[1]
            self._metronome = value[2]
            self._thirtyseconds = value[3]


class KeySignatureEvent(MetaEvent):
    """Key Signature meta event (``0x59``).

    Attributes:
        alternatives: Number of sharps (positive) or flats (negative).
        minor: ``0`` for major key, ``1`` for minor key.
    """
    __slots__ = ('_alternatives', '_minor')
    name: str = 'Key Signature'
    metacommand: int = 0x59
    length: int = 2

    def __init__(self, **kw: object) -> None:
        self._alternatives: int = 0
        self._minor: int = 0
        super().__init__(**kw)

    @property
    def alternatives(self) -> int:
        d = self._alternatives
        return d - 256 if d > 127 else d

    @alternatives.setter
    def alternatives(self, val: int) -> None:
        self._alternatives = 256 + val if val < 0 else val

    @property
    def minor(self) -> int: return self._minor
    @minor.setter
    def minor(self, val: int) -> None: self._minor = val

    @property
    def data(self) -> tuple[int, ...]:
        return (self._alternatives, self._minor)

    @data.setter
    def data(self, value) -> None:
        if len(value) >= 2:
            self._alternatives = value[0]
            self._minor = value[1]


class SequencerSpecificEvent(MetaEvent):
    """Sequencer-specific meta event (``0x7F``)."""
    __slots__ = ()
    name: str = 'Sequencer Specific'
    metacommand: int = 0x7F
    length: int = -1


__all__ = [
    'EventRegistry',
    'AbstractEvent', 'Event', 'MetaEvent', 'MetaEventWithText',
    'NoteEvent', 'NoteOnEvent', 'NoteOffEvent',
    'AfterTouchEvent', 'ControlChangeEvent',
    'ProgramChangeEvent', 'ChannelAfterTouchEvent',
    'PitchWheelEvent', 'SysexEvent',
    'SystemRealTimeEvent', 'ClockEvent', 'StartEvent',
    'ContinueEvent', 'StopEvent',
    'SongPositionPointerEvent',
    'SequenceNumberMetaEvent', 'TextMetaEvent',
    'CopyrightMetaEvent', 'TrackNameEvent',
    'InstrumentNameEvent', 'LyricsEvent', 'MarkerEvent',
    'CuePointEvent', 'ProgramNameEvent',
    'UnknownMetaEvent', 'ChannelPrefixEvent', 'PortEvent',
    'TrackLoopEvent', 'EndOfTrackEvent', 'SetTempoEvent',
    'SmpteOffsetEvent', 'TimeSignatureEvent',
    'KeySignatureEvent', 'SequencerSpecificEvent',
]
