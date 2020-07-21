from typing import List, Optional

from .events import Event


class Track(list):
    def __init__(self, events: Optional[List[Event]] = None, tick_relative: bool = True):
        self.tick_relative = tick_relative
        super(Track, self).__init__(events)

    def make_ticks_abs(self):
        if self.tick_relative:
            self.tick_relative = False
            running_tick = 0
            for event in self:
                event.tick += running_tick
                running_tick = event.tick

    def make_ticks_rel(self):
        if not self.tick_relative:
            self.tick_relative = True
            running_tick = 0
            for event in self:
                event.tick -= running_tick
                running_tick += event.tick

    def __getitem__(self, item):
        if isinstance(item, slice):
            indices = item.indices(len(self))
            return Track([super().__getitem__(i) for i in range(*indices)])
        else:
            return super(Track, self).__getitem__(item)

    def __getslice__(self, i, j):
        # The deprecated __getslice__ is still called when subclassing built-in types
        # for calls of the form List[i:j]
        return self.__getitem__(slice(i, j))

    def __repr__(self):
        return "midi.Track(\\\n [" + "\n  ".join(repr(event) for event in self) + "])"


class Pattern(list):
    def __init__(self,
                 tracks: Optional[List[Track]] = None,
                 midi_format: int = 1,
                 resolution: int = 220,
                 tick_relative: bool = True):
        self.format = midi_format
        self.resolution = resolution
        self.tick_relative = tick_relative
        super(Pattern, self).__init__(tracks or list())

    def __repr__(self):
        return f"midi.Pattern(format={self.format}, resolution={self.resolution}, tracks=\\\n{super().__repr__()})"

    def make_ticks_abs(self):
        self.tick_relative = False
        for track in self:
            track.make_ticks_abs()

    def make_ticks_rel(self):
        self.tick_relative = True
        for track in self:
            track.make_ticks_rel()

    def __getitem__(self, item):
        if isinstance(item, slice):
            indices = item.indices(len(self))
            return Pattern(resolution=self.resolution, midi_format=self.format,
                           tracks=[super().__getitem__(i) for i in range(*indices)])
        else:
            return super(Pattern, self).__getitem__(item)

    def __getslice__(self, i, j):
        # The deprecated __getslice__ is still called when subclassing built-in types
        # for calls of the form List[i:j]
        return self.__getitem__(slice(i, j))
