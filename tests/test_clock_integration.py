"""Integration test: two-process MIDI clock sync over real OS sequencer.

Spawns a source process that sends clock at a known BPM via a virtual port,
and a sink process that reads clock and estimates BPM. Validates sync.
"""
import subprocess
import sys
import json
import re

import pytest

PORT_NAME = 'python-midi-test-clock'
BPM = 130.0
DURATION = 4  # seconds

pytestmark = pytest.mark.skipif(
    sys.platform not in ('darwin', 'linux'),
    reason='Requires CoreMIDI (macOS) or ALSA (Linux)')


class TestClockSync:
    def test_source_sink_sync(self):
        """Two processes: source sends clock at known BPM,
        sink locks on and estimates BPM within tolerance."""

        # Start source
        source = subprocess.Popen(
            [sys.executable, 'tests/clock_source.py',
             str(BPM), str(DURATION), PORT_NAME],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

        # Wait for READY line
        ready_line = source.stdout.readline().strip()
        assert 'READY' in ready_line, f"Source didn't start: {ready_line}"

        # Build sink args (ALSA needs client:port from READY line)
        sink_args = [sys.executable, 'tests/clock_sink.py',
                      PORT_NAME, str(DURATION)]
        if sys.platform == 'linux':
            m = re.search(r'client=(\d+)\s+port=(\d+)', ready_line)
            assert m, f"No client:port in READY line: {ready_line}"
            sink_args.extend([m.group(1), m.group(2)])

        # Start sink
        sink = subprocess.Popen(
            sink_args,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

        # Wait for sink to connect
        connected_line = sink.stdout.readline().strip()
        assert 'CONNECTED' in connected_line, \
            f"Sink didn't connect: {connected_line}"

        # Signal source to start clocking
        source.stdin.write("GO\n")
        source.stdin.flush()

        # Wait for both
        source_out, source_err = source.communicate(timeout=DURATION + 10)
        sink_out, sink_err = sink.communicate(timeout=DURATION + 10)

        assert source.returncode == 0, f"Source failed: {source_err}"
        assert sink.returncode == 0, f"Sink failed: {sink_err}"

        # Parse sink JSON (last line)
        result = json.loads(sink_out.strip().splitlines()[-1])

        # BPM within 5%
        assert abs(result['bpm'] - BPM) / BPM < 0.05, \
            f"BPM mismatch: expected {BPM}, got {result['bpm']}"

        # Pulse count at least 80% of expected
        expected_pulses = BPM / 60.0 * 24 * DURATION
        assert result['pulses'] > expected_pulses * 0.8, \
            f"Too few pulses: {result['pulses']} (expected ~{expected_pulses})"
