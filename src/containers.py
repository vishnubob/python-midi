from pprint import pformat, pprint

class Pattern(list):
    def __init__(self, tracks=[], resolution=220, format=1):
        self.format = format
        self.resolution = resolution
        super(Pattern, self).__init__(tracks)

    def __repr__(self):
        return "midi.Pattern(format=%s, resolution=%s, tracks=\\\n%s)" % \
            (self.format, self.resolution, pformat(list(self)))

    def make_ticks_abs(self):
        for track in self:
            track.make_ticks_abs()

    def make_ticks_rel(self):
        for track in self:
            track.make_ticks_rel()

class Track(list):
    def make_ticks_abs(self):
        running_tick = 0
        for event in self:
            event.tick += running_tick
            running_tick = event.tick

    def make_ticks_rel(self):
        running_tick = 0
        for event in self:
            event.tick -= running_tick
            running_tick += event.tick
