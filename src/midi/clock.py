"""MIDI Clock — source and sink, platform-agnostic.

Uses only sequencer.event_write(event, tick=True) for output.
Works identically on CoreMIDI (macOS) and ALSA (Linux).
"""
from __future__ import annotations

import time

import midi


class ClockSource:
    """Clock source: schedules clock pulses via OS sequencer timestamps.

    Call schedule_ahead() from your run loop to keep the buffer full.
    The OS delivers each pulse at the exact kernel-scheduled time.
    """

    PPQ = 24  # pulses per quarter note (MIDI standard)

    def __init__(self, bpm: float = 120.0, sequencer: object = None) -> None:
        if sequencer is None:
            raise ValueError("sequencer is required")
        self._seq = sequencer
        self._bpm = bpm
        self._running = False
        self._pulse: int = 0          # total pulses scheduled since start
        self._scheduled: int = 0      # pulses already sent to sequencer
        self._start_tick: int = 0     # sequencer tick at start
        self._numerator: int = 4
        self._denominator: int = 4

    @property
    def bpm(self) -> float:
        return self._bpm

    @bpm.setter
    def bpm(self, value: float) -> None:
        self._bpm = value
        if self._running:
            self._seq.change_tempo(int(value))

    @property
    def running(self) -> bool:
        return self._running

    @property
    def pulse(self) -> int:
        return self._pulse

    @property
    def beat(self) -> float:
        return self._pulse / self.PPQ

    @property
    def bar(self) -> float:
        beats_per_bar = self._numerator * (4 / self._denominator)
        return self.beat / beats_per_bar

    def set_time_signature(self, numerator: int = 4, denominator: int = 4) -> None:
        self._numerator = numerator
        self._denominator = denominator

    def _ticks_per_pulse(self) -> float:
        """Sequencer ticks per MIDI clock pulse."""
        resolution = self._seq.sequencer_resolution
        return resolution / self.PPQ

    def tick_for_pulse(self, pulse: int) -> int:
        """Return the sequencer tick value for a given pulse number."""
        return self._start_tick + int(pulse * self._ticks_per_pulse())

    def start(self) -> None:
        """Send Start event and begin scheduling clock pulses."""
        self._seq.change_tempo(int(self._bpm))
        self._start_tick = self._seq.queue_get_tick_time()
        self._pulse = 0
        self._scheduled = 0
        self._running = True
        ev = midi.StartEvent()
        ev.tick = self._start_tick
        self._seq.event_write(ev, tick=True)

    def stop(self) -> None:
        """Send Stop event."""
        ev = midi.StopEvent()
        ev.tick = self._seq.queue_get_tick_time()
        self._seq.event_write(ev, tick=True)
        self._running = False

    def cont(self) -> None:
        """Send Continue event and resume scheduling."""
        self._running = True
        ev = midi.ContinueEvent()
        ev.tick = self._seq.queue_get_tick_time()
        self._seq.event_write(ev, tick=True)

    def schedule_ahead(self, pulses: int = 48) -> None:
        """Pre-schedule clock pulses into the future via event_write(tick=True).

        Only schedules pulses beyond what's already been scheduled.
        Call this periodically from your run loop.
        """
        if not self._running:
            return
        target = self._pulse + pulses
        while self._scheduled < target:
            ev = midi.ClockEvent()
            ev.tick = self.tick_for_pulse(self._scheduled)
            self._seq.event_write(ev, tick=True)
            self._scheduled += 1
        self._pulse = target


class ClockSink:
    """Clock sink: processes incoming clock events.

    Uses wall-clock time between ClockEvents for BPM estimation
    (exponential moving average). Feed events from event_read() into process().
    """

    PPQ = 24

    def __init__(self, sequencer_resolution: int) -> None:
        self._resolution = sequencer_resolution
        self._running = False
        self._pulse: int = 0
        self._last_tick: int | None = None
        self._last_time: float | None = None
        self._smoothed_interval: float | None = None  # seconds between pulses
        self._smoothed_tick_interval: float | None = None  # ticks between pulses
        self._alpha: float = 0.1  # EMA smoothing factor
        self._numerator: int = 4
        self._denominator: int = 4

    @property
    def running(self) -> bool:
        return self._running

    @property
    def pulse(self) -> int:
        return self._pulse

    @property
    def beat(self) -> float:
        return self._pulse / self.PPQ

    @property
    def bar(self) -> float:
        beats_per_bar = self._numerator * (4 / self._denominator)
        return self.beat / beats_per_bar

    def set_time_signature(self, numerator: int = 4, denominator: int = 4) -> None:
        self._numerator = numerator
        self._denominator = denominator

    @property
    def bpm(self) -> float:
        """Estimated BPM from wall-clock inter-pulse intervals."""
        if self._smoothed_interval is None or self._smoothed_interval <= 0:
            return 0.0
        seconds_per_beat = self._smoothed_interval * self.PPQ
        return 60.0 / seconds_per_beat

    def tick_for_next_pulse(self, offset: int = 0) -> int:
        """Predict tick for the next clock pulse (or +offset pulses ahead)."""
        if self._last_tick is None or self._smoothed_tick_interval is None:
            return 0
        return self._last_tick + int(self._smoothed_tick_interval * (1 + offset))

    def process(self, event: midi.AbstractEvent) -> None:
        """Feed events from event_read(). Recognizes Clock/Start/Stop/Continue/SPP."""
        if isinstance(event, midi.StartEvent):
            self._running = True
            self._pulse = 0
            self._last_tick = None
            self._last_time = None
            self._smoothed_interval = None
            self._smoothed_tick_interval = None
        elif isinstance(event, midi.StopEvent):
            self._running = False
        elif isinstance(event, midi.ContinueEvent):
            self._running = True
        elif isinstance(event, midi.SongPositionPointerEvent):
            # SPP position is in sixteenth notes; 1 sixteenth = 6 pulses
            self._pulse = event.position * 6
        elif isinstance(event, midi.ClockEvent):
            if self._running:
                now = time.monotonic()
                if self._last_time is not None:
                    dt = now - self._last_time
                    if dt > 0:
                        if self._smoothed_interval is None:
                            self._smoothed_interval = dt
                        else:
                            self._smoothed_interval = (
                                self._alpha * dt +
                                (1 - self._alpha) * self._smoothed_interval
                            )
                if self._last_tick is not None:
                    tick_delta = event.tick - self._last_tick
                    if tick_delta > 0:
                        if self._smoothed_tick_interval is None:
                            self._smoothed_tick_interval = float(tick_delta)
                        else:
                            self._smoothed_tick_interval = (
                                self._alpha * tick_delta +
                                (1 - self._alpha) * self._smoothed_tick_interval
                            )
                self._last_time = now
                self._last_tick = event.tick
                self._pulse += 1
