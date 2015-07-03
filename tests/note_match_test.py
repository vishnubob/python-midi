import midi


def standard_track():

    pattern = midi.Pattern()
    track = midi.Track()
    pattern.append(track)

    track.append(midi.NoteOnEvent(tick=0, velocity=20, pitch=midi.G_3))
    track.append(midi.NoteOnEvent(tick=10, velocity=30, pitch=midi.C_3))
    track.append(midi.NoteOnEvent(tick=50, velocity=0, pitch=midi.C_3))
    track.append(midi.NoteOffEvent(tick=100, pitch=midi.G_3))

    track.append(midi.NoteOnEvent(tick=50, velocity=10, pitch=midi.D_3))
    track.append(midi.NoteOffEvent(tick=50, velocity=10, pitch=midi.D_3))
    track.append(midi.NoteOnEvent(tick=0, velocity=20, pitch=midi.D_3))
    track.append(midi.NoteOffEvent(tick=50, velocity=20, pitch=midi.D_3))

    # Add the end of track event, append it to the track
    eot = midi.EndOfTrackEvent(tick=1)
    track.append(eot)

    # Print out the pattern
    print pattern


    # Save the pattern to disk
    #midi.write_midifile("example.mid", pattern)

    return pattern
