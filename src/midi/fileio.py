"""MIDI file I/O — read and write Standard MIDI Files."""
from __future__ import annotations

from collections.abc import Iterator
from struct import unpack, pack
from typing import BinaryIO
from warnings import warn

from .containers import *
from .events import *
from .constants import *
from .util import *


class FileReader:
    def read(self, midifile: BinaryIO) -> Pattern:
        pattern = self.parse_file_header(midifile)
        for track in pattern:
            self.parse_track(midifile, track)
        return pattern

    def parse_file_header(self, midifile: BinaryIO) -> Pattern:
        # First four bytes are MIDI header
        magic = midifile.read(4)
        if magic != b'MThd':
            raise TypeError("Bad header in MIDI file.")
        # next four bytes are header size
        # next two bytes specify the format version
        # next two bytes specify the number of tracks
        # next two bytes specify the resolution/PPQ/Parts Per Quarter
        # (in other words, how many ticks per quater note)
        data = unpack(">LHHH", midifile.read(10))
        hdrsz = data[0]
        format = data[1]
        tracks = [Track() for x in range(data[2])]
        resolution = data[3]
        # XXX: the assumption is that any remaining bytes
        # in the header are padding
        if hdrsz > DEFAULT_MIDI_HEADER_SIZE:
            midifile.read(hdrsz - DEFAULT_MIDI_HEADER_SIZE)
        return Pattern(tracks=tracks, resolution=resolution, format=format)

    def parse_track_header(self, midifile: BinaryIO) -> int:
        # First four bytes are Track header
        magic = midifile.read(4)
        if magic != b'MTrk':
            raise TypeError("Bad track header in MIDI file: " + repr(magic))
        # next four bytes are track size
        trksz = unpack(">L", midifile.read(4))[0]
        return trksz

    def parse_track(self, midifile: BinaryIO, track: Track) -> None:
        self.RunningStatus = None
        trksz = self.parse_track_header(midifile)
        trackdata = iter(midifile.read(trksz))
        while True:
            try:
                event = self.parse_midi_event(trackdata)
                track.append(event)
            except StopIteration:
                break

    def parse_midi_event(self, trackdata: Iterator[int]) -> AbstractEvent:
        # first datum is varlen representing delta-time
        tick = read_varlen(trackdata)
        # next byte is status message
        stsmsg = next(trackdata)
        # is the event a MetaEvent?
        if MetaEvent.is_event(stsmsg):
            cmd = next(trackdata)
            if cmd not in EventRegistry.MetaEvents:
                warn(f"Unknown Meta MIDI Event: {cmd}", Warning)
                cls = UnknownMetaEvent
            else:
                cls = EventRegistry.MetaEvents[cmd]
            datalen = read_varlen(trackdata)
            data = [next(trackdata) for x in range(datalen)]
            return cls(tick=tick, data=data, metacommand=cmd)
        # is this event a Sysex Event?
        elif SysexEvent.is_event(stsmsg):
            data = []
            while True:
                datum = next(trackdata)
                if datum == 0xF7:
                    break
                data.append(datum)
            return SysexEvent(tick=tick, data=data)
        # not a Meta MIDI event or a Sysex event, must be a general message
        else:
            key = stsmsg & 0xF0
            if key not in EventRegistry.Events:
                if not self.RunningStatus:
                    raise ValueError("Bad byte value")
                data = []
                key = self.RunningStatus & 0xF0
                ev_cls = EventRegistry.Events[key]
                channel = self.RunningStatus & 0x0F
                data.append(stsmsg)
                data += [next(trackdata) for x in range(ev_cls.length - 1)]
                return ev_cls(tick=tick, channel=channel, data=data)
            else:
                self.RunningStatus = stsmsg
                ev_cls = EventRegistry.Events[key]
                channel = self.RunningStatus & 0x0F
                data = [next(trackdata) for x in range(ev_cls.length)]
                return ev_cls(tick=tick, channel=channel, data=data)
        # unreachable — all branches return above


class FileWriter:
    def write(self, midifile: BinaryIO, pattern: Pattern) -> None:
        self.write_file_header(midifile, pattern)
        for track in pattern:
            self.write_track(midifile, track)

    def write_file_header(self, midifile: BinaryIO, pattern: Pattern) -> None:
        # First four bytes are MIDI header
        packdata = pack(">LHHH", 6,
                            pattern.format,
                            len(pattern),
                            pattern.resolution)
        midifile.write(b'MThd' + packdata)

    def write_track(self, midifile: BinaryIO, track: Track) -> None:
        buf = b''
        self.RunningStatus = None
        for event in track:
            buf += self.encode_midi_event(event)
        buf = self.encode_track_header(len(buf)) + buf
        midifile.write(buf)

    def encode_track_header(self, trklen: int) -> bytes:
        return b'MTrk' + pack(">L", trklen)

    def encode_midi_event(self, event: AbstractEvent) -> bytes:
        ret = b''
        ret += write_varlen(event.tick)
        # is the event a MetaEvent?
        if isinstance(event, MetaEvent):
            ret += bytes([event.statusmsg, event.metacommand])
            ret += write_varlen(len(event.data))
            ret += bytes(event.data)
        # is this event a Sysex Event?
        elif isinstance(event, SysexEvent):
            ret += bytes([0xF0])
            ret += bytes(event.data)
            ret += bytes([0xF7])
        # not a Meta MIDI event or a Sysex event, must be a general message
        elif isinstance(event, Event):
            if not self.RunningStatus or \
                self.RunningStatus.statusmsg != event.statusmsg or \
                self.RunningStatus.channel != event.channel:
                    self.RunningStatus = event
                    ret += bytes([event.statusmsg | event.channel])
            ret += bytes(event.data)
        else:
            raise ValueError("Unknown MIDI Event: " + str(event))
        return ret


def write_midifile(midifile: str | BinaryIO, pattern: Pattern) -> None:
    """Write a Pattern to a Standard MIDI File.

    Args:
        midifile: Destination file path or an open binary file object.
        pattern: The Pattern to write.
    """
    if isinstance(midifile, str):
        midifile = open(midifile, 'wb')
    with midifile:
        writer = FileWriter()
        writer.write(midifile, pattern)


def read_midifile(midifile: str | BinaryIO) -> Pattern:
    """Read a Standard MIDI File into a Pattern.

    Args:
        midifile: Path to a ``.mid`` file, or an open binary file object.

    Returns:
        A Pattern containing one Track per MIDI track in the file.
        Ticks are relative (delta times) by default.

    Raises:
        TypeError: If the file header is not valid MIDI.
    """
    if isinstance(midifile, str):
        midifile = open(midifile, 'rb')
    with midifile:
        reader = FileReader()
        return reader.read(midifile)
