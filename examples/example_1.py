import midi
# Instantiate a MIDI Pattern (contains a list of tracks)
pattern = midi.Pattern()
# Instantiate a MIDI Track (contains a list of MIDI events)
pattern.append(midi.Track((
    midi.TimeSignatureEvent(tick=0,numerator=4,denominator=4,
                            metronome=24,
                            thirtyseconds=8),
    midi.KeySignatureEvent(tick=0),
    midi.EndOfTrackEvent(tick=1) 
    )))
track = midi.Track()
pattern.append(track)
#reverb
#track.append(midi.ControlChangeEvent(tick=0,data=[91,58]))
#track.append(midi.ControlChangeEvent(tick=0,data=[10,69]))
#msb
#track.append(midi.ControlChangeEvent(tick=0,channel=0,data=[0,0]))
#lsb
#track.append(midi.ControlChangeEvent(tick=0,channel=0,data=[32,0]))
#track.append(midi.ProgramChangeEvent(tick=0,channel=0,data=[24]))
# Instantiate a MIDI note on event, append it to the track
track.append(midi.NoteOnEvent(tick=0, velocity=200, pitch=midi.G_4))
# Instantiate a MIDI note off event, append it to the track
track.append(midi.NoteOffEvent(tick=250, velocity=200, pitch=midi.G_4))
track.append(midi.EndOfTrackEvent(tick=100))
# some more notes
pattern.append(midi.Track((
    midi.NoteOnEvent(tick=200, velocity=200, pitch=(midi.F_4+1)),
    midi.NoteOnEvent(tick=200, velocity=200, pitch=midi.A_4),
    midi.NoteOnEvent(tick=200, velocity=200, pitch=midi.C_5),
    midi.EndOfTrackEvent(tick=1))))
# Add the end of track event, append it to the track
# Print out the pattern
print(pattern)
# Save the pattern to disk
midi.write_midifile("example.mid", pattern)
