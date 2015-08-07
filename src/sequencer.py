class TempoMap(list):
    def __init__(self, resolution):
        self.resolution = resolution

    def add_and_update(self, event):
        self.add(event)
        self.update()

    def add(self, event):
        # get tempo in microseconds per beat
        tempo = event.mpqn
        # convert into milliseconds per beat
        tempo = tempo / 1000.0
        # generate ms per tick
        event.mpt = tempo / self.resolution
        self.append(event)

    def update(self):
        self.sort()
        # adjust running time
        last = None
        for event in self:
            if last:
                event.msdelay = last.msdelay + \
                    int(last.mpt * (event.tick - last.tick))
            last = event

    def get_tempo(self, offset=0):
        try:
            last = self[0]
            for tm in self[1:]:
                if tm.tick > offset:
                    return last
                last = tm
            return last
        except IndexError:
            # no tempo changes specified in midi track
            last = SetTempoEvent()
            last.bpm = 120
            last.mpqn = 500
            last.mpt = last.mpqn / self.resolution
            self.append(last)
            return last

class TimeResolver(object):
    """
    iterates over a pattern and analyzes timing information
    the result of the analysis can be used to convert from absolute midi tick to wall clock time (in milliseconds).
    """
    def __init__(self, pattern):
        self.pattern = pattern
        self.tempomap = TempoMap(self.pattern.resolution)
        self.__resolve_timing()

    def __resolve_timing(self):
        """
        go over all events and initialize a tempo map
        """
        # backup original mode and turn to absolute
        original_ticks_relative = self.pattern.tick_relative
        self.pattern.make_ticks_abs()
        # create a tempo map
        self.__init_tempomap()
        # restore original mode
        if (original_ticks_relative):
            self.pattern.make_ticks_rel()

    def __init_tempomap(self):
        """
        initialize the tempo map which tracks tempo changes through time 
        """
        for track in self.pattern:
            for event in track:
                if event.name == "Set Tempo":
                    self.tempomap.add(event)
        self.tempomap.update()

    def tick2ms(self, absolute_tick):
        """
        convert absolute midi tick to wall clock time (milliseconds)
        """
        ev = self.tempomap.get_tempo(absolute_tick)
        ms = ev.msdelay + ((absolute_tick - ev.tick)*ev.mpt)
        return ms

class EventStreamIterator(object):
    def __init__(self, stream, window):
        self.stream = stream
        self.trackpool = stream.trackpool
        self.window_length = window
        self.window_edge = 0
        self.leftover = None
        self.events = self.stream.iterevents()
        # First, need to look ahead to see when the
        # tempo markers end
        self.ttpts = []
        for tempo in stream.tempomap[1:]:
            self.ttpts.append(tempo.tick)
        # Finally, add the end of track tick.
        self.ttpts.append(stream.endoftrack.tick)
        self.ttpts = iter(self.ttpts)
        # Setup next tempo timepoint
        self.ttp = next(self.ttpts)
        self.tempomap = iter(self.stream.tempomap)
        self.tempo = next(self.tempomap)
        self.endoftrack = False

    def __iter__(self):
        return self

    def __next_edge(self):
        if self.endoftrack:
            raise StopIteration
        lastedge = self.window_edge
        self.window_edge += int(self.window_length / self.tempo.mpt)
        if self.window_edge > self.ttp:
            # We're past the tempo-marker.
            oldttp = self.ttp
            try:
                self.ttp = next(self.ttpts)
            except StopIteration:
                # End of Track!
                self.window_edge = self.ttp
                self.endoftrack = True
                return
            # Calculate the next window edge, taking into
            # account the tempo change.
            msused = (oldttp - lastedge) * self.tempo.mpt
            msleft = self.window_length - msused
            self.tempo = next(self.tempomap)
            ticksleft = msleft / self.tempo.mpt
            self.window_edge = ticksleft + self.tempo.tick

    def __next__(self):
        ret = []
        self.__next_edge()
        if self.leftover:
            if self.leftover.tick > self.window_edge:
                return ret
            ret.append(self.leftover)
            self.leftover = None
        for event in self.events:
            if event.tick > self.window_edge:
                self.leftover = event
                return ret
            ret.append(event)
        return ret

