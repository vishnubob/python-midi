import midi
import midi.sequencer as sequencer

pattern = midi.read_file("mary.mid")
pattern.make_ticks_abs()
timeresolver = sequencer.TimeResolver(pattern)
for track in pattern:
    for event in track:
        tick = event.tick
        milliseconds = timeresolver.tick2ms(tick)
        print ("event {2} at tick {0} happens {1} ms after starting the piece".format(tick, milliseconds, event.name))

