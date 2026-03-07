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
    __slots__ = ('tick', 'data')
    name: str = "Generic MIDI Event"
    length: int | str = 0
    statusmsg: int = 0x0

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls.__name__ not in ('Event', 'MetaEvent', 'NoteEvent',
                                'MetaEventWithText'):
            EventRegistry.register_event(cls, cls.__mro__)

    def __init__(self, **kw: object) -> None:
        if isinstance(self.length, int):
            defdata = [0] * self.length
        else:
            defdata = []
        self.tick: int = 0
        self.data: list[int] = defdata
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
    __slots__ = ('channel',)
    name: str = 'Event'
    channel: int

    def __init__(self, **kw: object) -> None:
        if 'channel' not in kw:
            kw = kw.copy()
            kw['channel'] = 0
        super().__init__(**kw)

    def copy(self, **kw: object) -> Event:
        _kw: dict[str, object] = {'channel': self.channel, 'tick': self.tick, 'data': self.data}
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
    __slots__ = ()
    statusmsg: int = 0xFF
    metacommand: int = 0x0
    name: str = 'Meta Event'

    @classmethod
    def is_event(cls, statusmsg: int) -> bool:
        return (statusmsg == 0xFF)


class NoteEvent(Event):
    __slots__ = ()
    length: int = 2

    @property
    def pitch(self) -> int:
        return self.data[0]

    @pitch.setter
    def pitch(self, val: int) -> None:
        self.data[0] = val

    @property
    def velocity(self) -> int:
        return self.data[1]

    @velocity.setter
    def velocity(self, val: int) -> None:
        self.data[1] = val


class NoteOnEvent(NoteEvent):
    __slots__ = ()
    statusmsg: int = 0x90
    name: str = 'Note On'

class NoteOffEvent(NoteEvent):
    __slots__ = ()
    statusmsg: int = 0x80
    name: str = 'Note Off'

class AfterTouchEvent(Event):
    __slots__ = ()
    statusmsg: int = 0xA0
    length: int = 2
    name: str = 'After Touch'

    @property
    def pitch(self) -> int:
        return self.data[0]

    @pitch.setter
    def pitch(self, val: int) -> None:
        self.data[0] = val

    @property
    def value(self) -> int:
        return self.data[1]

    @value.setter
    def value(self, val: int) -> None:
        self.data[1] = val


class ControlChangeEvent(Event):
    __slots__ = ()
    statusmsg: int = 0xB0
    length: int = 2
    name: str = 'Control Change'

    @property
    def control(self) -> int:
        return self.data[0]

    @control.setter
    def control(self, val: int) -> None:
        self.data[0] = val

    @property
    def value(self) -> int:
        return self.data[1]

    @value.setter
    def value(self, val: int) -> None:
        self.data[1] = val


class ProgramChangeEvent(Event):
    __slots__ = ()
    statusmsg: int = 0xC0
    length: int = 1
    name: str = 'Program Change'

    @property
    def value(self) -> int:
        return self.data[0]

    @value.setter
    def value(self, val: int) -> None:
        self.data[0] = val


class ChannelAfterTouchEvent(Event):
    __slots__ = ()
    statusmsg: int = 0xD0
    length: int = 1
    name: str = 'Channel After Touch'

    @property
    def value(self) -> int:
        return self.data[0]

    @value.setter
    def value(self, val: int) -> None:
        self.data[0] = val


class PitchWheelEvent(Event):
    __slots__ = ()
    statusmsg: int = 0xE0
    length: int = 2
    name: str = 'Pitch Wheel'

    @property
    def pitch(self) -> int:
        return ((self.data[1] << 7) | self.data[0]) - 0x2000

    @pitch.setter
    def pitch(self, pitch: int) -> None:
        value = pitch + 0x2000
        self.data[0] = value & 0x7F
        self.data[1] = (value >> 7) & 0x7F


class SysexEvent(Event):
    __slots__ = ()
    statusmsg: int = 0xF0
    name: str = 'SysEx'
    length: str = 'varlen'

    @classmethod
    def is_event(cls, statusmsg: int) -> bool:
        return (cls.statusmsg == statusmsg)


class SequenceNumberMetaEvent(MetaEvent):
    __slots__ = ()
    name: str = 'Sequence Number'
    metacommand: int = 0x00
    length: int = 2

class MetaEventWithText(MetaEvent):
    __slots__ = ('text',)
    text: str

    def __init__(self, **kw: object) -> None:
        super().__init__(**kw)
        if 'text' not in kw:
            self.text = ''.join(chr(datum) for datum in self.data)

    def __repr__(self) -> str:
        return self.__baserepr__(['text'])

class TextMetaEvent(MetaEventWithText):
    __slots__ = ()
    name: str = 'Text'
    metacommand: int = 0x01
    length: str = 'varlen'

class CopyrightMetaEvent(MetaEventWithText):
    __slots__ = ()
    name: str = 'Copyright Notice'
    metacommand: int = 0x02
    length: str = 'varlen'

class TrackNameEvent(MetaEventWithText):
    __slots__ = ()
    name: str = 'Track Name'
    metacommand: int = 0x03
    length: str = 'varlen'

class InstrumentNameEvent(MetaEventWithText):
    __slots__ = ()
    name: str = 'Instrument Name'
    metacommand: int = 0x04
    length: str = 'varlen'

class LyricsEvent(MetaEventWithText):
    __slots__ = ()
    name: str = 'Lyrics'
    metacommand: int = 0x05
    length: str = 'varlen'

class MarkerEvent(MetaEventWithText):
    __slots__ = ()
    name: str = 'Marker'
    metacommand: int = 0x06
    length: str = 'varlen'

class CuePointEvent(MetaEventWithText):
    __slots__ = ()
    name: str = 'Cue Point'
    metacommand: int = 0x07
    length: str = 'varlen'

class ProgramNameEvent(MetaEventWithText):
    __slots__ = ()
    name: str = 'Program Name'
    metacommand: int = 0x08
    length: str = 'varlen'

class UnknownMetaEvent(MetaEvent):
    __slots__ = ('_metacommand',)
    name: str = 'Unknown'
    metacommand: int | None = None

    def __init__(self, **kw: object) -> None:
        self._metacommand: int = kw.pop('metacommand')
        super(MetaEvent, self).__init__(**kw)

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
    __slots__ = ()
    name: str = 'Channel Prefix'
    metacommand: int = 0x20
    length: int = 1

class PortEvent(MetaEvent):
    __slots__ = ()
    name: str = 'MIDI Port/Cable'
    metacommand: int = 0x21

class TrackLoopEvent(MetaEvent):
    __slots__ = ()
    name: str = 'Track Loop'
    metacommand: int = 0x2E

class EndOfTrackEvent(MetaEvent):
    __slots__ = ()
    name: str = 'End of Track'
    metacommand: int = 0x2F

class SetTempoEvent(MetaEvent):
    __slots__ = ()
    name: str = 'Set Tempo'
    metacommand: int = 0x51
    length: int = 3

    @property
    def bpm(self) -> float:
        return float(6e7) / self.mpqn

    @bpm.setter
    def bpm(self, bpm: float) -> None:
        self.mpqn = int(float(6e7) / bpm)

    @property
    def mpqn(self) -> int:
        assert(len(self.data) == 3)
        vals = [self.data[x] << (16 - (8 * x)) for x in range(3)]
        return sum(vals)

    @mpqn.setter
    def mpqn(self, val: int) -> None:
        self.data = [(val >> (16 - (8 * x)) & 0xFF) for x in range(3)]

class SmpteOffsetEvent(MetaEvent):
    __slots__ = ()
    name: str = 'SMPTE Offset'
    metacommand: int = 0x54

class TimeSignatureEvent(MetaEvent):
    __slots__ = ()
    name: str = 'Time Signature'
    metacommand: int = 0x58
    length: int = 4

    @property
    def numerator(self) -> int:
        return self.data[0]

    @numerator.setter
    def numerator(self, val: int) -> None:
        self.data[0] = val

    @property
    def denominator(self) -> int:
        return 2 ** self.data[1]

    @denominator.setter
    def denominator(self, val: int) -> None:
        self.data[1] = int(math.log(val, 2))

    @property
    def metronome(self) -> int:
        return self.data[2]

    @metronome.setter
    def metronome(self, val: int) -> None:
        self.data[2] = val

    @property
    def thirtyseconds(self) -> int:
        return self.data[3]

    @thirtyseconds.setter
    def thirtyseconds(self, val: int) -> None:
        self.data[3] = val


class KeySignatureEvent(MetaEvent):
    __slots__ = ()
    name: str = 'Key Signature'
    metacommand: int = 0x59
    length: int = 2

    @property
    def alternatives(self) -> int:
        d = self.data[0]
        return d - 256 if d > 127 else d

    @alternatives.setter
    def alternatives(self, val: int) -> None:
        self.data[0] = 256 + val if val < 0 else val

    @property
    def minor(self) -> int:
        return self.data[1]

    @minor.setter
    def minor(self, val: int) -> None:
        self.data[1] = val


class SequencerSpecificEvent(MetaEvent):
    __slots__ = ()
    name: str = 'Sequencer Specific'
    metacommand: int = 0x7F
