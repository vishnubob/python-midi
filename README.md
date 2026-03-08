# Python MIDI

**[Documentation](https://python-midi.readthedocs.io/)**

Python, for all its amazing ability out of the box, does not provide you with
an easy means to manipulate MIDI data. There are probably about ten different
python packages out there that accomplish some part of this goal, but there is
nothing that is totally comprehensive.

This toolkit aims to fulfill this goal. In particular, it strives to provide a
high level framework that is independent of hardware. It tries to offer a
reasonable object granularity to make MIDI streams a painless thing to
manipulate, sequence, record, and playback. It's important to have a good
concept of time, and the event framework provides automatic hooks so you don't
have to calculate ticks to wall clock, for example.

## Features

- High level class types that represent individual MIDI events.
- A multi-track aware container, that allows you to manage your MIDI events.
- A tempo map that actively keeps track of tempo changes within a track.
- A reader and writer, so you can read and write your MIDI tracks to disk.

## Installation

Requires [Python 3.10+](https://docs.python.org/3/):

```
pip install .
```

### Examine a MIDI File

To examine the contents of a MIDI file run

```
$ mididump mary.mid
```

This will print out a representation of "Mary had a Little Lamb" as executable python code.

## Example Usage

### Building a MIDI File from scratch

It is easy to build a MIDI track from scratch.

```python
import midi
# Instantiate a MIDI Pattern (contains a list of tracks)
pattern = midi.Pattern()
# Instantiate a MIDI Track (contains a list of MIDI events)
track = midi.Track()
# Append the track to the pattern
pattern.append(track)
# Instantiate a MIDI note on event, append it to the track
on = midi.NoteOnEvent(tick=0, velocity=20, pitch=midi.note_value('G_3'))
track.append(on)
# Instantiate a MIDI note off event, append it to the track
off = midi.NoteOffEvent(tick=100, pitch=midi.note_value('G_3'))
track.append(off)
# Add the end of track event, append it to the track
eot = midi.EndOfTrackEvent(tick=1)
track.append(eot)
# Print out the pattern
print(pattern)
# Save the pattern to disk
midi.write_midifile("example.mid", pattern)
```

A MIDI file is represented as a hierarchical set of objects. At the top is a
Pattern, which contains a list of Tracks, and a Track is a list of MIDI Events.

The MIDI Pattern class implements the MutableSequence interface (acts like a
list -- supports indexing, iteration, append, slicing -- but is not a list
subclass). Patterns also contain global MIDI metadata: the resolution and MIDI
Format.

The MIDI Track class also implements the MutableSequence interface. It does not
have any special metadata like Pattern, but it does provide a few helper
functions to manipulate all events within a track.

There are 27 different MIDI Events supported. In this example, three different
MIDI events are created and added to the MIDI Track:

- The **NoteOnEvent** captures the start of note, like a piano player pushing down on a piano key. The tick is when this event occurred, the pitch is the note value of the key pressed, and the velocity represents how hard the key was pressed.

- The **NoteOffEvent** captures the end of note, just like a piano player removing her finger from a depressed piano key. Once again, the tick is when this event occurred, the pitch is the note that is released, and the velocity has no real world analogy and is usually ignored. NoteOnEvents with a velocity of zero are equivalent to NoteOffEvents.

- The **EndOfTrackEvent** is a special event, and is used to indicate to MIDI sequencing software when the song ends. With creating Patterns with multiple Tracks, you only need one EndOfTrack event for the entire song. Most MIDI software will refuse to load a MIDI file if it does not contain an EndOfTrack event.

You might notice that the EndOfTrackEvent has a tick value of 1. This is
because MIDI represents ticks in relative time. The actual tick offset of the
MidiTrackEvent is the sum of its tick and all the ticks from previous events.
In this example, the EndOfTrackEvent would occur at tick 101 (0 + 100 + 1).

#### Side Note: What is a MIDI Tick?

The problem with ticks is that they don't give you any information about when
they occur without knowing two other pieces of information, the resolution, and
the tempo. The code handles these issues for you so all you have to do is
think about things in terms of milliseconds, or ticks, if you care about the beat.

A tick represents the lowest level resolution of a MIDI track. Tempo is always
analogous with Beats per Minute (BPM) which is the same thing as Quarter notes
per Minute (QPM). The Resolution is also known as the Pulses per Quarter note
(PPQ). It analogous to Ticks per Beat (TPM).

Tempo is set by two things. First, a saved MIDI file encodes an initial
Resolution and Tempo. You use these values to initialize the sequencer timer.
The Resolution should be considered static to a track, as well as the
sequencer. During MIDI playback, the MIDI file may have encoded sequenced
(that is, timed) Tempo change events. These events will modulate the Tempo at
the time they specify. The Resolution, however, can not change from its
initial value during playback.

Under the hood, MIDI represents Tempo in microseconds. In other words, you
convert Tempo to Microseconds per Beat. If the Tempo was 120 BPM, the python
code to convert to microseconds looks like this:

```python
>>> 60 * 1000000 / 120
500000
```

This says the Tempo is 500,000 microseconds per beat. This, in combination
with the Resolution, will allow you to convert ticks to time. If there are
500,000 microseconds per beat, and if the Resolution is 1,000 than one tick is
how much time?

```python
>>> 500000 / 1000
500
>>> 500 / 1000000.0
0.0005
```

In other words, one tick represents .0005 seconds of time or half a
millisecond. Increase the Resolution and this number gets smaller, the inverse
as the Resolution gets smaller. Same for Tempo.

Although MIDI encodes Time Signatures, it has no impact on the Tempo. However,
here is a quick refresher on Time Signatures:

https://en.wikipedia.org/wiki/Time_signature

### Reading our Track back from Disk

It's just as easy to load your MIDI file from disk.

```python
import midi
pattern = midi.read_midifile("example.mid")
print(pattern)
```

## Sequencer

The toolkit includes sequencer support for real-time MIDI I/O:

- **Linux**: ALSA sequencer via SWIG wrapper
- **macOS**: CoreMIDI sequencer via pure ctypes (no compilation needed)

The appropriate backend is selected automatically based on your platform.
The sequencer understands the higher level Event framework, and will convert
these Events to structures accessible to the platform API. It tries to do as
much of the hard work for you as possible, including adjusting the queue for
tempo changes during playback. You can also record MIDI events, and the
sequencer will timestamp your MIDI tracks at the moment the event triggers an
OS hardware interrupt. The timing is extremely accurate, even though you are
using Python to manage it.

### Scripts for Sequencer

To examine the hardware and software MIDI devices attached to your
system, run the `mididumphw` command.

```
$ mididumphw
```

To play a MIDI file:

```
$ midiplay <client> <port> <midi_file>
```

To record MIDI input to a file:

```
$ midirecord <source_endpoint_ref> <output.mid> [duration_seconds]
```

To listen to a MIDI device and print events:

```
$ midilisten <client> <port>
```

## Website, support, bug tracking, development etc.

You can find the latest code on the home page:
https://github.com/vishnubob/python-midi/

You can also check for known issues and submit new ones to the
tracker: https://github.com/vishnubob/python-midi/issues/

## Thanks

I originally wrote this to drive the electro-mechanical instruments of Ensemble
Robot, which is a Boston based group of artists, programmers, and engineers.
This API, however, has applications beyond controlling this equipment. For
more information about Ensemble Robot, please visit:

http://www.ensemblerobot.org/
