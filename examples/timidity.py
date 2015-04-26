#!/usr/bin/env pypy
import midi
import subprocess as s

def main():
    p = s.Popen(["timidity","-"],stdin=s.PIPE)
    writer = midi.FileWriter(p.stdin)
    writer.write_file_header(midi.Pattern())
    writer.write_track_header(1)

    def song():
        for i in range(200):
            yield midi.NoteOnEvent(tick=i*100, velocity=200, pitch=midi.G_3)
    for event in song():
        writer.write_midi_event(event)
    p.stdin.close()
    p.wait()
    
    
    
if __name__ == '__main__':
    main()
