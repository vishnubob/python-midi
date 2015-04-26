#!/usr/bin/env pypy
import midi
import subprocess as s

def main():
    p = s.Popen(["timidity"]+['--verbose']*1+["-"],stdin=s.PIPE)
    writer = midi.FileWriter(p.stdin)
    writer.write_file_header(midi.Pattern(),2)

    def song():
        for i in range(5):
            yield midi.NoteOnEvent(tick=i*100, velocity=200, pitch=(midi.G_5+i))
        yield midi.EndOfTrackEvent(tick=1)
    writer.write_track(midi.Track(song()))
    p.stdin.flush()
    p.stdin.close()
    p.wait()
    
    
    
if __name__ == '__main__':
    main()
