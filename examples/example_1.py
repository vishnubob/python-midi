import midi
# Instantiate a MIDI Pattern (contains a list of tracks)
pattern = midi.Pattern()
# Instantiate a MIDI Track (contains a list of MIDI events)
track = midi.Track()
# Append the track to the pattern
pattern.append(track)
track.append(midi.TimeSignatureEvent(tick=0,numerator=4,denominator=4,
                                     metronome=24,
                                     thirtyseconds=8))
track.append(midi.KeySignatureEvent(tick=0))
track = midi.Track()
#reverb
track.append(midi.ControlChangeEvent(tick=0,data=[91,58]))
track.append(midi.ControlChangeEvent(tick=0,data=[10,69]))
#msb
track.append(midi.ControlChangeEvent(tick=0,channel=0,data=[0,0]))
#lsb
track.append(midi.ControlChangeEvent(tick=0,channel=0,data=[0,0]))
track.append(midi.ProgramChangeEvent(tick=0,channel=0,data=[24]))
# Instantiate a MIDI note on event, append it to the track
on = midi.NoteOnEvent(tick=0, channel=0, data=[43,20])
on = midi.NoteOnEvent(tick=10, channel=0, data=[43,20])
on = midi.NoteOnEvent(tick=100, channel=0, data=[43,20])
on = midi.NoteOnEvent(tick=200, channel=0, data=[43,20])
track.append(on)
# Instantiate a MIDI note off event, append it to the track
off = midi.NoteOffEvent(tick=1000, data=[43,0])
track.append(off)
# Add the end of track event, append it to the track
eot = midi.EndOfTrackEvent(tick=1)
track.append(eot)
# Print out the pattern
print(pattern)
# Save the pattern to disk
midi.write_midifile("example.mid", pattern)
