import midi 

def read_varlen(data):
    NEXTBYTE = 1
    value = 0
    while NEXTBYTE:
        chr = ord(data.next())
        # is the hi-bit set?
        if not (chr & 0x80):
            # no next BYTE
            NEXTBYTE = 0
        # mask out the 8th bit
        chr = chr & 0x7f
        # shift last value up 7 bits
        value = value << 7
        # add new value
        value += chr
    return value

def write_varlen(value):
    chr1 = chr(value & 0x7F)
    value >>= 7
    if value:
        chr2 = chr((value & 0x7F) | 0x80)
        value >>= 7
        if value:
            chr3 = chr((value & 0x7F) | 0x80)
            value >>= 7
            if value:
                chr4 = chr((value & 0x7F) | 0x80)
                res = chr4 + chr3 + chr2 + chr1
            else:
                res = chr3 + chr2 + chr1
        else:
            res = chr2 + chr1
    else:
        res = chr1
    return res


def find_matching_note_off(track, noteOnEvent):
    """
    Given a track and a NoteOn event, find the matching NoteOff event (if any).
    
    This works for either NoteOff events, or NoteOn events with Velocity=0,
    which is the obnoxious and common alternative to using NoteOff events.

    Algorithm:
    - Walk each event in the track
      - If it's before the tick of the NoteOn event, ignore it
      - If it's a NoteOn event with a non-zero velocity, ignore it because this
        cannot be a "NoteOff" event.
      - If it's a NoteOn event with the same channel + pitch and zero velocity, return it
      - If it's a NoteOff event with the same channel + pitch, return it

    More information: See https://github.com/vishnubob/python-midi/issues/56
    """

    # use absolute ticks
    track.make_ticks_abs()

    # first, make sure the noteOnEvent is actually a NoteOn event
    if not isinstance(noteOnEvent, midi.NoteOnEvent):
        return None

    # also, make sure it has a velocity, otherwise it could be a 
    # a NoteOn event that's actually masquerading as a NoteOff event
    if noteOnEvent.velocity == 0:
        return None

    for event in track:

        # ignore anything that's not a NoteEvent
        if not isinstance(event, midi.NoteEvent):
            continue

        # If it's before the tick of the NoteOn event, ignore it
        if event.tick < noteOnEvent.tick:
            continue

        # If it's a NoteOn event with a non-zero velocity, ignore it because this
        # cannot be a "NoteOff" event.
        if isinstance(event, midi.NoteOnEvent) and event.velocity != 0:
            continue 

        # If it's a NoteOn event with the same channel + pitch and zero velocity, return it
        if isinstance(event, midi.NoteOnEvent) and \
           matching_pitch_chan(event, noteOnEvent) and \
           event.velocity == 0:
            return event 
        
        # If it's a NoteOff event with the same channel + pitch, return it
        if isinstance(event, midi.NoteOffEvent) and \
           matching_pitch_chan(event, noteOnEvent):
            return event
        
        
def matching_pitch_chan(noteEvent, otherNoteEvent):

    if not isinstance(noteEvent, midi.NoteEvent):
        return False
    if not isinstance(otherNoteEvent, midi.NoteEvent):
        return False
    if noteEvent.channel != otherNoteEvent.channel:
        return False 
    if noteEvent.pitch != otherNoteEvent.pitch:
        return False 
    return True 
