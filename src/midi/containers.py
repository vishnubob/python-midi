from __future__ import annotations

from collections.abc import MutableSequence, Iterable
from pprint import pformat
from typing import overload

from .events import AbstractEvent


class Pattern(MutableSequence['Track']):
    def __init__(self, tracks: Iterable[Track] | None = None,
                 resolution: int = 220, format: int = 1,
                 tick_relative: bool = True) -> None:
        self.format = format
        self.resolution = resolution
        self.tick_relative = tick_relative
        self._tracks: list[Track] = list(tracks) if tracks is not None else []

    @overload
    def __getitem__(self, index: int) -> Track: ...
    @overload
    def __getitem__(self, index: slice) -> Pattern: ...
    def __getitem__(self, index: int | slice) -> Track | Pattern:
        if isinstance(index, slice):
            return Pattern(resolution=self.resolution, format=self.format,
                           tracks=self._tracks[index])
        return self._tracks[index]

    @overload
    def __setitem__(self, index: int, value: Track) -> None: ...
    @overload
    def __setitem__(self, index: slice, value: Iterable[Track]) -> None: ...
    def __setitem__(self, index: int | slice, value: Track | Iterable[Track]) -> None:
        self._tracks[index] = value

    def __delitem__(self, index: int | slice) -> None:
        del self._tracks[index]

    def __len__(self) -> int:
        return len(self._tracks)

    def insert(self, index: int, value: Track) -> None:
        self._tracks.insert(index, value)

    def sort(self, *, key=None, reverse: bool = False) -> None:
        self._tracks.sort(key=key, reverse=reverse)

    def __repr__(self) -> str:
        return "midi.Pattern(format=%r, resolution=%r, tracks=\\\n%s)" % \
            (self.format, self.resolution, pformat(list(self)))

    def make_ticks_abs(self) -> None:
        self.tick_relative = False
        for track in self:
            track.make_ticks_abs()

    def make_ticks_rel(self) -> None:
        self.tick_relative = True
        for track in self:
            track.make_ticks_rel()


class Track(MutableSequence[AbstractEvent]):
    def __init__(self, events: Iterable[AbstractEvent] | None = None,
                 tick_relative: bool = True) -> None:
        self.tick_relative = tick_relative
        self._events: list[AbstractEvent] = list(events) if events is not None else []

    @overload
    def __getitem__(self, index: int) -> AbstractEvent: ...
    @overload
    def __getitem__(self, index: slice) -> Track: ...
    def __getitem__(self, index: int | slice) -> AbstractEvent | Track:
        if isinstance(index, slice):
            return Track(self._events[index])
        return self._events[index]

    @overload
    def __setitem__(self, index: int, value: AbstractEvent) -> None: ...
    @overload
    def __setitem__(self, index: slice, value: Iterable[AbstractEvent]) -> None: ...
    def __setitem__(self, index: int | slice, value: AbstractEvent | Iterable[AbstractEvent]) -> None:
        self._events[index] = value

    def __delitem__(self, index: int | slice) -> None:
        del self._events[index]

    def __len__(self) -> int:
        return len(self._events)

    def insert(self, index: int, value: AbstractEvent) -> None:
        self._events.insert(index, value)

    def sort(self, *, key=None, reverse: bool = False) -> None:
        self._events.sort(key=key, reverse=reverse)

    def make_ticks_abs(self) -> None:
        if self.tick_relative:
            self.tick_relative = False
            running_tick = 0
            for event in self:
                event.tick += running_tick
                running_tick = event.tick

    def make_ticks_rel(self) -> None:
        if not self.tick_relative:
            self.tick_relative = True
            running_tick = 0
            for event in self:
                event.tick -= running_tick
                running_tick += event.tick

    def __repr__(self) -> str:
        return "midi.Track(\\\n  %s)" % (pformat(list(self)).replace('\n', '\n  '), )
