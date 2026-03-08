"""Tests for midi.clock — ClockSource and ClockSink."""
from __future__ import annotations

import sys
import os
import time
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

import midi
from midi.clock import ClockSource, ClockSink


class MockSequencer:
    """Captures events written via event_write for testing."""

    def __init__(self, sequencer_resolution: int = 1000, tick: int = 0) -> None:
        self.sequencer_resolution = sequencer_resolution
        self._tick = tick
        self.events: list[tuple[midi.AbstractEvent, dict]] = []
        self.tempo: int = 120

    def queue_get_tick_time(self) -> int:
        return self._tick

    def event_write(self, event, **kwargs) -> int:
        self.events.append((event, kwargs))
        return 65536

    def change_tempo(self, tempo: int) -> bool:
        self.tempo = tempo
        return True


class TestClockSource:
    def test_requires_sequencer(self):
        try:
            ClockSource(bpm=120)
            assert False, "Should raise ValueError"
        except ValueError:
            pass

    def test_initial_state(self):
        seq = MockSequencer()
        clock = ClockSource(bpm=120, sequencer=seq)
        assert clock.bpm == 120
        assert not clock.running
        assert clock.pulse == 0
        assert clock.beat == 0.0
        assert clock.bar == 0.0

    def test_start_sends_start_event(self):
        seq = MockSequencer()
        clock = ClockSource(bpm=120, sequencer=seq)
        clock.start()
        assert clock.running
        assert len(seq.events) == 1
        ev, kw = seq.events[0]
        assert isinstance(ev, midi.StartEvent)
        assert kw == {'tick': True}

    def test_stop_sends_stop_event(self):
        seq = MockSequencer()
        clock = ClockSource(bpm=120, sequencer=seq)
        clock.start()
        clock.stop()
        assert not clock.running
        ev, kw = seq.events[-1]
        assert isinstance(ev, midi.StopEvent)

    def test_cont_sends_continue_event(self):
        seq = MockSequencer()
        clock = ClockSource(bpm=120, sequencer=seq)
        clock.start()
        clock.stop()
        clock.cont()
        assert clock.running
        ev, kw = seq.events[-1]
        assert isinstance(ev, midi.ContinueEvent)

    def test_schedule_ahead_creates_clock_events(self):
        seq = MockSequencer(sequencer_resolution=24)
        clock = ClockSource(bpm=120, sequencer=seq)
        clock.start()
        seq.events.clear()
        clock.schedule_ahead(24)
        assert len(seq.events) == 24
        for ev, kw in seq.events:
            assert isinstance(ev, midi.ClockEvent)
            assert kw == {'tick': True}

    def test_schedule_ahead_evenly_spaced(self):
        seq = MockSequencer(sequencer_resolution=24)
        clock = ClockSource(bpm=120, sequencer=seq)
        clock.start()
        seq.events.clear()
        clock.schedule_ahead(24)
        ticks = [ev.tick for ev, _ in seq.events]
        # resolution=24, PPQ=24 → 1 tick per pulse
        for i in range(1, len(ticks)):
            assert ticks[i] - ticks[i - 1] == 1

    def test_schedule_ahead_higher_resolution(self):
        seq = MockSequencer(sequencer_resolution=480)
        clock = ClockSource(bpm=120, sequencer=seq)
        clock.start()
        seq.events.clear()
        clock.schedule_ahead(24)
        ticks = [ev.tick for ev, _ in seq.events]
        # 480 / 24 = 20 ticks per pulse
        for i in range(1, len(ticks)):
            assert ticks[i] - ticks[i - 1] == 20

    def test_schedule_ahead_idempotent(self):
        seq = MockSequencer(sequencer_resolution=24)
        clock = ClockSource(bpm=120, sequencer=seq)
        clock.start()
        seq.events.clear()
        clock.schedule_ahead(24)
        count1 = len(seq.events)
        # Calling again schedules more pulses (advances _pulse)
        clock.schedule_ahead(24)
        count2 = len(seq.events) - count1
        assert count2 == 24  # 24 more new pulses

    def test_pulse_advances(self):
        seq = MockSequencer(sequencer_resolution=24)
        clock = ClockSource(bpm=120, sequencer=seq)
        clock.start()
        clock.schedule_ahead(24)
        assert clock.pulse == 24
        assert clock.beat == 1.0

    def test_schedule_ahead_noop_when_stopped(self):
        seq = MockSequencer()
        clock = ClockSource(bpm=120, sequencer=seq)
        clock.schedule_ahead(48)
        assert len(seq.events) == 0

    def test_tick_for_pulse(self):
        seq = MockSequencer(sequencer_resolution=480, tick=100)
        clock = ClockSource(bpm=120, sequencer=seq)
        clock.start()
        # start_tick = 100, ticks_per_pulse = 480/24 = 20
        assert clock.tick_for_pulse(0) == 100
        assert clock.tick_for_pulse(1) == 120
        assert clock.tick_for_pulse(24) == 580  # 100 + 24*20

    def test_bpm_change(self):
        seq = MockSequencer(sequencer_resolution=24)
        clock = ClockSource(bpm=120, sequencer=seq)
        clock.bpm = 140
        assert clock.bpm == 140

    def test_start_calls_change_tempo(self):
        seq = MockSequencer(sequencer_resolution=24)
        clock = ClockSource(bpm=130, sequencer=seq)
        clock.start()
        assert seq.tempo == 130

    def test_bpm_change_while_running_calls_change_tempo(self):
        seq = MockSequencer(sequencer_resolution=24)
        clock = ClockSource(bpm=120, sequencer=seq)
        clock.start()
        clock.bpm = 140
        assert seq.tempo == 140

    def test_bar_with_time_signature(self):
        seq = MockSequencer(sequencer_resolution=24)
        clock = ClockSource(bpm=120, sequencer=seq)
        clock.set_time_signature(3, 4)
        clock.start()
        clock.schedule_ahead(72)  # 72 pulses = 3 beats
        assert clock.beat == 3.0
        assert clock.bar == 1.0

    def test_bar_default_4_4(self):
        seq = MockSequencer(sequencer_resolution=24)
        clock = ClockSource(bpm=120, sequencer=seq)
        clock.start()
        clock.schedule_ahead(96)  # 96 pulses = 4 beats
        assert clock.beat == 4.0
        assert clock.bar == 1.0


class TestClockSink:
    def test_initial_state(self):
        sink = ClockSink(sequencer_resolution=1000)
        assert not sink.running
        assert sink.pulse == 0
        assert sink.bpm == 0.0

    def test_start_sets_running(self):
        sink = ClockSink(sequencer_resolution=1000)
        sink.process(midi.StartEvent())
        assert sink.running
        assert sink.pulse == 0

    def test_stop_clears_running(self):
        sink = ClockSink(sequencer_resolution=1000)
        sink.process(midi.StartEvent())
        sink.process(midi.StopEvent())
        assert not sink.running

    def test_continue_sets_running(self):
        sink = ClockSink(sequencer_resolution=1000)
        sink.process(midi.StartEvent())
        sink.process(midi.StopEvent())
        sink.process(midi.ContinueEvent())
        assert sink.running

    def test_clock_increments_pulse(self):
        sink = ClockSink(sequencer_resolution=1000)
        sink.process(midi.StartEvent())
        for _ in range(24):
            sink.process(midi.ClockEvent())
        assert sink.pulse == 24
        assert sink.beat == 1.0

    def test_clock_only_counts_when_running(self):
        sink = ClockSink(sequencer_resolution=1000)
        # Not running — clock events ignored
        sink.process(midi.ClockEvent())
        assert sink.pulse == 0

    def test_spp_sets_position(self):
        sink = ClockSink(sequencer_resolution=1000)
        ev = midi.SongPositionPointerEvent()
        ev.position = 16  # 16 sixteenth notes = 96 pulses
        sink.process(ev)
        assert sink.pulse == 96

    def test_bpm_estimation(self):
        sink = ClockSink(sequencer_resolution=1000)
        sink.process(midi.StartEvent())
        # Simulate 120 BPM: 24 PPQ, so pulse interval = 60/120/24 = 0.02083s
        interval = 60.0 / 120.0 / 24
        # Feed enough pulses for the EMA to converge
        for i in range(50):
            ev = midi.ClockEvent()
            ev.tick = i * 42  # tick values (not used for BPM calc)
            # Manually set the internal time to simulate wall clock
            sink._last_time = i * interval if i > 0 else None
            if i > 0:
                # Simulate process() with controlled timing
                now = (i + 1) * interval
                dt = now - sink._last_time
                if sink._smoothed_interval is None:
                    sink._smoothed_interval = dt
                else:
                    sink._smoothed_interval = (
                        sink._alpha * dt +
                        (1 - sink._alpha) * sink._smoothed_interval
                    )
                sink._last_time = now
                sink._pulse += 1
            else:
                sink._last_time = 0.0
                sink._pulse += 1
        # Should converge close to 120 BPM
        assert abs(sink.bpm - 120.0) < 1.0

    def test_tick_for_next_pulse(self):
        sink = ClockSink(sequencer_resolution=1000)
        sink.process(midi.StartEvent())
        # Manually set internal state
        sink._last_tick = 100
        sink._smoothed_tick_interval = 42.0
        assert sink.tick_for_next_pulse() == 142  # 100 + 42*1
        assert sink.tick_for_next_pulse(offset=1) == 184  # 100 + 42*2

    def test_tick_for_next_pulse_no_data(self):
        sink = ClockSink(sequencer_resolution=1000)
        assert sink.tick_for_next_pulse() == 0

    def test_start_resets_state(self):
        sink = ClockSink(sequencer_resolution=1000)
        sink.process(midi.StartEvent())
        sink._pulse = 100
        sink._smoothed_interval = 0.02
        sink.process(midi.StartEvent())
        assert sink.pulse == 0
        assert sink._smoothed_interval is None

    def test_bar_with_time_signature(self):
        sink = ClockSink(sequencer_resolution=1000)
        sink.set_time_signature(3, 4)
        sink.process(midi.StartEvent())
        for _ in range(72):  # 3 beats * 24 PPQ
            sink.process(midi.ClockEvent())
        assert sink.beat == 3.0
        assert sink.bar == 1.0

    def test_ignores_unrelated_events(self):
        sink = ClockSink(sequencer_resolution=1000)
        sink.process(midi.StartEvent())
        ev = midi.NoteOnEvent(channel=0)
        ev.pitch, ev.velocity = 60, 100
        sink.process(ev)  # should not raise
        assert sink.pulse == 0
