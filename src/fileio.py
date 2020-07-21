from struct import unpack, pack
from typing import BinaryIO, Union
from warnings import warn

from src.constants import DEFAULT_MIDI_HEADER_SIZE
from src.containers import Track, Pattern
from src.events import MetaEvent, EventRegistry, UnknownMetaEvent, SysexEvent, Event
from src.util import read_varlen, write_varlen


class FileReader(object):
    def read(self, midi_file: BinaryIO):
        pattern = self.parse_file_header(midi_file)
        for track in pattern:
            self.parse_track(midi_file, track)
        return pattern

    def parse_file_header(self, midi_file: BinaryIO):
        # First four bytes are MIDI header
        chunk_type = midi_file.read(4)
        if chunk_type != b'MThd':
            raise TypeError("Bad header in MIDI file.")
        # next four bytes are header size
        # next two bytes specify the format version
        # next two bytes specify the number of tracks
        # next two bytes specify the resolution/PPQ/Parts Per Quarter
        # (in other words, how many ticks per quarter note)
        data = unpack(">LHHH", midi_file.read(10))
        header_size = data[0]
        midi_format = data[1]
        tracks = [Track() for x in range(data[2])]
        resolution = data[3]
        # XXX: the assumption is that any remaining bytes
        # in the header are padding
        if header_size > DEFAULT_MIDI_HEADER_SIZE:
            midi_file.read(header_size - DEFAULT_MIDI_HEADER_SIZE)
        return Pattern(tracks=tracks, resolution=resolution, midi_format=midi_format)

    def parse_track_header(self, midi_file: BinaryIO):
        # First four bytes are Track header
        chunk_type = midi_file.read(4)
        if chunk_type != b'MTrk':
            raise TypeError("Bad track header in MIDI file.")
        # next four bytes are track size
        track_size = unpack(">L", midi_file.read(4))[0]
        return track_size

    def parse_track(self, midi_file: BinaryIO, track: Track):
        self.RunningStatus = None
        track_size = self.parse_track_header(midi_file)
        track_data = iter(bytearray(midi_file.read(track_size)))
        while True:
            try:
                event = self.parse_midi_event(track_data)
                track.append(event)
            except StopIteration:
                break

    def parse_midi_event(self, track_data):
        # first datum is varlen representing delta-time
        tick = read_varlen(track_data)
        # next byte is status message
        status_message = next(track_data)
        # is the event a MetaEvent?
        if MetaEvent.is_event(status_message):
            cmd = next(track_data)
            if cmd not in EventRegistry.MetaEvents:
                warn("Unknown Meta MIDI Event: " + repr(cmd), Warning)
                cls = UnknownMetaEvent
            else:
                cls = EventRegistry.MetaEvents[cmd]
            data_len = read_varlen(track_data)
            data = [next(track_data) for x in range(data_len)]
            return cls(tick=tick, data=data, metacommand=cmd)
        # is this event a Sysex Event?
        elif SysexEvent.is_event(status_message):
            data = []
            while True:
                datum = next(track_data)
                if datum == 0xF7:
                    break
                data.append(datum)
            return SysexEvent(tick=tick, data=data)
        # not a Meta MIDI event or a Sysex event, must be a general message
        else:
            key = status_message & 0xF0
            if key not in EventRegistry.Events:
                assert self.RunningStatus, "Bad byte value"
                data = []
                key = self.RunningStatus & 0xF0
                cls = EventRegistry.Events[key]
                channel = self.RunningStatus & 0x0F
                data.append(status_message)
                data += [next(track_data) for x in range(cls.length - 1)]
                return cls(tick=tick, channel=channel, data=data)
            else:
                self.RunningStatus = status_message
                cls = EventRegistry.Events[key]
                channel = self.RunningStatus & 0x0F
                data = [next(track_data) for x in range(cls.length)]
                return cls(tick=tick, channel=channel, data=data)


class FileWriter(object):
    def write(self, midi_file: BinaryIO, pattern: Pattern):
        self.write_file_header(midi_file, pattern)
        for track in pattern:
            self.write_track(midi_file, track)

    def write_file_header(self, midi_file: BinaryIO, pattern: Pattern):
        # First four bytes are MIDI header
        packed_data = pack(">LHHH", 6,
                           pattern.format,
                           len(pattern),
                           pattern.resolution)
        midi_file.write(b'MThd' + packed_data)

    def write_track(self, midi_file: BinaryIO, track: Track):
        buf = []
        self.RunningStatus = None
        for event in track:
            buf.append(self.encode_midi_event(event))
        buf = b"".join(buf)
        buf = self.encode_track_header(len(buf)) + buf
        midi_file.write(buf)

    def encode_track_header(self, track_len: int):
        return b'MTrk' + pack(">L", track_len)

    def encode_midi_event(self, event: Event):
        ret = bytearray()
        ret += write_varlen(event.tick)
        # is the event a MetaEvent?
        if isinstance(event, MetaEvent):
            ret += bytearray([event.statusmsg, event.metacommand])
            ret += write_varlen(len(event.data))
            ret += bytearray(event.data)
        # is this event a Sysex Event?
        elif isinstance(event, SysexEvent):
            ret.append(0xF0)
            ret += bytearray(event.data)
            ret.append(0xF7)
        # not a Meta MIDI event or a Sysex event, must be a general message
        elif isinstance(event, Event):
            if not self.RunningStatus or \
                    self.RunningStatus.statusmsg != event.statusmsg or \
                    self.RunningStatus.channel != event.channel:
                self.RunningStatus = event
                ret.append(event.statusmsg | event.channel)
            ret += bytearray(event.data)
        else:
            raise ValueError("Unknown MIDI Event: " + str(event))
        return ret


def write_midifile(midi_file: Union[BinaryIO, str], pattern: Pattern) -> None:
    manually_open = False

    if not hasattr(midi_file, "write"):
        manually_open = True
        midi_file = open(midi_file, 'wb')

    try:
        writer = FileWriter()
        writer.write(midi_file, pattern)
    finally:
        if manually_open:
            midi_file.close()


def read_midifile(midi_file: Union[BinaryIO, str]) -> Pattern:
    manually_open = False

    if not hasattr(midi_file, "read"):
        manually_open = True
        midi_file = open(midi_file, 'rb')

    try:
        reader = FileReader()
        data = reader.read(midi_file)
    finally:
        if manually_open:
            midi_file.close()

    return data
