"""Tests for System Real-Time and Song Position Pointer events."""
from __future__ import annotations

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

import midi
from midi.events import EventRegistry


class TestSystemRealTimeEvents:
    def test_clock_event(self):
        ev = midi.ClockEvent()
        assert ev.statusmsg == 0xF8
        assert ev.name == 'Clock'
        assert ev.length == 0
        assert ev.data == ()

    def test_start_event(self):
        ev = midi.StartEvent()
        assert ev.statusmsg == 0xFA
        assert ev.name == 'Start'
        assert ev.length == 0
        assert ev.data == ()

    def test_continue_event(self):
        ev = midi.ContinueEvent()
        assert ev.statusmsg == 0xFB
        assert ev.name == 'Continue'
        assert ev.length == 0
        assert ev.data == ()

    def test_stop_event(self):
        ev = midi.StopEvent()
        assert ev.statusmsg == 0xFC
        assert ev.name == 'Stop'
        assert ev.length == 0
        assert ev.data == ()

    def test_not_in_event_registry(self):
        for status in (0xF8, 0xFA, 0xFB, 0xFC):
            assert status not in EventRegistry.Events
        assert 0xF2 not in EventRegistry.Events
        for cls in (midi.ClockEvent, midi.StartEvent, midi.ContinueEvent,
                    midi.StopEvent, midi.SongPositionPointerEvent):
            assert cls not in EventRegistry.MetaEvents.values()

    def test_tick_default(self):
        ev = midi.ClockEvent()
        assert ev.tick == 0

    def test_tick_kwarg(self):
        ev = midi.ClockEvent(tick=42)
        assert ev.tick == 42


class TestSongPositionPointerEvent:
    def test_basic(self):
        ev = midi.SongPositionPointerEvent()
        assert ev.statusmsg == 0xF2
        assert ev.name == 'Song Position Pointer'
        assert ev.length == 2
        assert ev.data == (0, 0)

    def test_position_roundtrip(self):
        ev = midi.SongPositionPointerEvent()
        for pos in (0, 1, 127, 128, 1000, 16383):
            ev.position = pos
            assert ev.position == pos

    def test_position_encoding(self):
        ev = midi.SongPositionPointerEvent()
        ev.position = 300  # 300 = 0x12C → LSB=0x2C, MSB=0x02
        assert ev.data[0] == 300 & 0x7F   # 0x2C = 44
        assert ev.data[1] == (300 >> 7) & 0x7F  # 0x02 = 2

    def test_not_in_registry(self):
        assert 0xF2 not in EventRegistry.Events


class TestCoreMIDIRoundTrip:
    """Test _build_midi_bytes / _parse_midi_bytes for real-time events."""

    def _get_funcs(self):
        try:
            from midi.sequencer_osx.sequencer import _build_midi_bytes, _parse_midi_bytes
            return _build_midi_bytes, _parse_midi_bytes
        except ImportError:
            import pytest
            pytest.skip("CoreMIDI not available")

    def test_clock_roundtrip(self):
        build, parse = self._get_funcs()
        ev = midi.ClockEvent()
        raw = build(ev)
        assert raw == bytes([0xF8])
        parsed = parse(raw, 0)
        assert isinstance(parsed, midi.ClockEvent)

    def test_start_roundtrip(self):
        build, parse = self._get_funcs()
        ev = midi.StartEvent()
        raw = build(ev)
        assert raw == bytes([0xFA])
        parsed = parse(raw, 0)
        assert isinstance(parsed, midi.StartEvent)

    def test_continue_roundtrip(self):
        build, parse = self._get_funcs()
        ev = midi.ContinueEvent()
        raw = build(ev)
        assert raw == bytes([0xFB])
        parsed = parse(raw, 0)
        assert isinstance(parsed, midi.ContinueEvent)

    def test_stop_roundtrip(self):
        build, parse = self._get_funcs()
        ev = midi.StopEvent()
        raw = build(ev)
        assert raw == bytes([0xFC])
        parsed = parse(raw, 0)
        assert isinstance(parsed, midi.StopEvent)

    def test_spp_roundtrip(self):
        build, parse = self._get_funcs()
        ev = midi.SongPositionPointerEvent()
        ev.position = 500
        raw = build(ev)
        assert raw[0] == 0xF2
        parsed = parse(raw, 0)
        assert isinstance(parsed, midi.SongPositionPointerEvent)
        assert parsed.position == 500
