"""Clock source subprocess: creates a virtual MIDI port and sends clock at a known BPM.

Usage: python tests/clock_source.py <bpm> <duration_sec> <port_name>

Protocol: prints READY, waits for GO on stdin, then starts clocking.
"""
import sys
import time

sys.path.insert(0, 'src')

import midi
from midi.clock import ClockSource

bpm, duration, port_name = float(sys.argv[1]), float(sys.argv[2]), sys.argv[3]

if sys.platform == 'darwin':
    from midi.sequencer_osx.sequencer import SequencerWrite
    seq = SequencerWrite(sequencer_resolution=1000)
    seq.create_virtual_source(port_name)
else:
    from midi.sequencer_alsa.sequencer import SequencerWrite
    seq = SequencerWrite(alsa_sequencer_name=port_name,
                         sequencer_resolution=1000)

seq.start_sequencer()

if sys.platform == 'darwin':
    sys.stdout.write("READY\n")
else:
    sys.stdout.write(f"READY client={seq.client_id} port={seq.port}\n")
sys.stdout.flush()

# Wait for orchestrator to signal that sink is connected
line = sys.stdin.readline().strip()
assert line == 'GO', f"Expected GO, got: {line}"

clock = ClockSource(bpm=bpm, sequencer=seq)
clock.start()

deadline = time.monotonic() + duration
while time.monotonic() < deadline:
    clock.schedule_ahead(48)
    time.sleep(0.25)

clock.stop()
time.sleep(0.5)  # let sink drain
sys.stdout.write(f"DONE pulses={clock.pulse}\n")
sys.stdout.flush()
