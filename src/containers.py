from pprint import pformat, pprint

class Pattern(list):
    def __init__(self, tracks=[], resolution=220, format=1):
        self.format = format
        self.resolution = resolution
        super(Pattern, self).__init__(tracks)

    def __repr__(self):
        return "midi.Pattern(format=%r, resolution=%r, tracks=\\\n%s)" % \
            (self.format, self.resolution, pformat(list(self)))

    def make_ticks_abs(self):
        for track in self:
            track.make_ticks_abs()

    def make_ticks_rel(self):
        for track in self:
            track.make_ticks_rel()
            
    def __getitem__(self, item):
        if isinstance(item, slice):
            indices = item.indices(len(self))
            return Pattern(resolution=self.resolution, format=self.format,
                            tracks=(super(Pattern, self).__getitem__(i) for i in xrange(*indices)))
        else:
            return super(Pattern, self).__getitem__(item)
            
    def __getslice__(self, i, j):
        # The deprecated __getslice__ is still called when subclassing built-in types
        # for calls of the form List[i:j]
        return self.__getitem__(slice(i,j))

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

    def __getitem__(self, item):
        if isinstance(item, slice):
            indices = item.indices(len(self))
            return Track((super(Track, self).__getitem__(i) for i in xrange(*indices)))
        else:
            return super(Track, self).__getitem__(item)
            
    def __getslice__(self, i, j):
        # The deprecated __getslice__ is still called when subclassing built-in types
        # for calls of the form List[i:j]
        return self.__getitem__(slice(i,j))

    def __repr__(self):
        return "midi.Track(\\\n  %s)" % (pformat(list(self)).replace('\n', '\n  '), )
