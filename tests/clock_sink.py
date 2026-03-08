"""Clock sink subprocess: reads MIDI clock from a virtual port and estimates BPM.

Usage: python tests/clock_sink.py <port_name> <duration_sec> [client_id port_id]
"""
import sys
import time
import json

sys.path.insert(0, 'src')

import midi
from midi.clock import ClockSink

port_name, duration = sys.argv[1], float(sys.argv[2])

if sys.platform == 'darwin':
    from midi.sequencer_osx.sequencer import SequencerRead, find_source_by_name
    # Poll until virtual source appears
    source = None
    deadline = time.monotonic() + 10
    while source is None and time.monotonic() < deadline:
        source = find_source_by_name(port_name)
        if source is None:
            time.sleep(0.1)
    assert source is not None, f"Source '{port_name}' not found"
    seq = SequencerRead(sequencer_resolution=1000)
    seq.subscribe_port(0, source)
else:
    from midi.sequencer_alsa.sequencer import SequencerRead
    client_id, port_id = int(sys.argv[3]), int(sys.argv[4])
    seq = SequencerRead(sequencer_resolution=1000)
    seq.subscribe_port(client_id, port_id)

seq.start_sequencer()
sys.stdout.write("CONNECTED\n")
sys.stdout.flush()

sink = ClockSink(sequencer_resolution=1000)
deadline = time.monotonic() + duration
while time.monotonic() < deadline:
    ev = seq.event_read()
    if ev is not None:
        sink.process(ev)
    else:
        time.sleep(0.001)

result = json.dumps({
    "pulses": sink.pulse,
    "bpm": round(sink.bpm, 2),
    "running": sink.running,
    "beats": round(sink.beat, 2),
})
sys.stdout.write(result + "\n")
sys.stdout.flush()
