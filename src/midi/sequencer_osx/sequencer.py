"""macOS CoreMIDI sequencer with tick-accurate playback and recording.

Mirrors the ALSA sequencer API for cross-platform compatibility.
"""
from __future__ import annotations

import threading
import time
from collections import deque

import midi
from . import coremidi as cm


class Sequencer:
    SEQUENCER_TYPE = "coremidi"

    def __init__(self, *, sequencer_name: str = "python-midi",
                 sequencer_tempo: int = 120,
                 sequencer_resolution: int = 1000) -> None:
        self.sequencer_tempo = sequencer_tempo
        self.sequencer_resolution = sequencer_resolution
        self._queue_running = False
        self._start_host_time: int = 0
        self._start_wall_time: float = 0.0
        self._client = cm.midi_client_create(sequencer_name)
        self._output_port: cm.MIDIPortRef | None = None
        self._input_port: cm.MIDIPortRef | None = None
        self._dest_endpoint: cm.MIDIEndpointRef | None = None
        self._source_endpoint: cm.MIDIEndpointRef | None = None
        self._read_queue: deque[midi.Event] = deque()
        self._read_proc: cm.MIDIReadProc | None = None

    def __del__(self) -> None:
        try:
            cm.midi_client_dispose(self._client)
        except Exception:
            pass

    def _usec_per_tick(self) -> float:
        return (60_000_000.0 / self.sequencer_tempo) / self.sequencer_resolution

    def _tick_to_host_time(self, tick: int) -> int:
        nanos = int(tick * self._usec_per_tick() * 1000)
        return self._start_host_time + cm.nanos_to_host_time(nanos)

    def _host_time_to_tick(self, host_time: int) -> int:
        elapsed_nanos = cm.host_time_to_nanos(host_time - self._start_host_time)
        usec_per_tick = self._usec_per_tick()
        return int(elapsed_nanos / (usec_per_tick * 1000))

    def start_sequencer(self) -> None:
        if not self._queue_running:
            self._start_host_time = cm.mach_absolute_time()
            self._start_wall_time = time.time()
            self._queue_running = True

    def stop_sequencer(self) -> None:
        self._queue_running = False

    def continue_sequencer(self) -> None:
        if not self._queue_running:
            self._queue_running = True

    def change_tempo(self, tempo: int) -> bool:
        self.sequencer_tempo = tempo
        return True

    def queue_get_tick_time(self) -> int:
        if not self._queue_running:
            return 0
        return self._host_time_to_tick(cm.mach_absolute_time())

    def queue_get_real_time(self) -> tuple[int, int]:
        if not self._queue_running:
            return (0, 0)
        now_nanos = cm.host_time_to_nanos(
            cm.mach_absolute_time() - self._start_host_time)
        sec = int(now_nanos // 1_000_000_000)
        nsec = int(now_nanos % 1_000_000_000)
        return (sec, nsec)

    def drain(self) -> None:
        pass  # CoreMIDI handles delivery

    def drop_output(self) -> None:
        pass  # No output buffer to flush

    def output_pending(self) -> int:
        return 0

    def subscribe_port(self, client: int, port: int) -> None:
        raise NotImplementedError("Subclasses must implement subscribe_port")


class SequencerHardware(Sequencer):
    """Enumerate CoreMIDI devices, sources, and destinations."""

    class Client:
        def __init__(self, device_ref: cm.MIDIDeviceRef, name: str) -> None:
            self.client = device_ref
            self.name = name
            self._ports: dict[str, SequencerHardware.Client.Port] = {}

        def __str__(self) -> str:
            retstr = '] client(%d) "%s"\n' % (self.client, self.name)
            for port in self:
                retstr += str(port)
            return retstr

        def add_port(self, port_ref: int, name: str, caps: int) -> None:
            if name in self._ports:
                existing = self._ports[name]
                existing.caps |= caps
                existing.caps_read = bool(existing.caps & self.Port.CAP_READ)
                existing.caps_write = bool(existing.caps & self.Port.CAP_WRITE)
                if caps & self.Port.CAP_READ:
                    existing.source_ref = port_ref
                if caps & self.Port.CAP_WRITE:
                    existing.dest_ref = port_ref
            else:
                port = self.Port(port_ref, name, caps)
                self._ports[name] = port

        def __iter__(self):
            return iter(self._ports.values())

        def __len__(self) -> int:
            return len(self._ports)

        def get_port(self, key: str) -> SequencerHardware.Client.Port:
            return self._ports[key]
        __getitem__ = get_port

        class Port:
            CAP_READ = 1
            CAP_WRITE = 2

            def __init__(self, port: int, name: str, caps: int) -> None:
                self.port = port          # primary ref (backward compat)
                self.name = name
                self.caps = caps
                self.source_ref = port if (caps & self.CAP_READ) else None
                self.dest_ref = port if (caps & self.CAP_WRITE) else None
                self.caps_read = bool(caps & self.CAP_READ)
                self.caps_write = bool(caps & self.CAP_WRITE)

            def __str__(self) -> str:
                flags = []
                if self.caps_read:
                    flags.append('r')
                if self.caps_write:
                    flags.append('w')
                flags_str = ', '.join(flags)
                refs = []
                if self.source_ref is not None:
                    refs.append('source=%d' % self.source_ref)
                if self.dest_ref is not None:
                    refs.append('dest=%d' % self.dest_ref)
                refs_str = ' (%s)' % ', '.join(refs) if refs else ''
                return ']   port [%s] "%s"%s\n' % (flags_str, self.name, refs_str)

    def __init__(self, **kw) -> None:
        super().__init__(**kw)
        self._clients: dict[str, SequencerHardware.Client] = {}
        self._enumerate()

    def _enumerate(self) -> None:
        num_devices = cm.get_number_of_devices()
        for i in range(num_devices):
            device = cm.get_device(i)
            name = cm.get_device_name(device)
            client = self.Client(device, name)
            num_entities = cm._coremidi.MIDIDeviceGetNumberOfEntities(device)
            for j in range(num_entities):
                entity = cm._coremidi.MIDIDeviceGetEntity(device, j)
                # Sources (readable)
                num_srcs = cm._coremidi.MIDIEntityGetNumberOfSources(entity)
                for k in range(num_srcs):
                    ep = cm._coremidi.MIDIEntityGetSource(entity, k)
                    ep_name = cm.get_endpoint_name(ep)
                    client.add_port(ep, ep_name, self.Client.Port.CAP_READ)
                # Destinations (writable)
                num_dests = cm._coremidi.MIDIEntityGetNumberOfDestinations(entity)
                for k in range(num_dests):
                    ep = cm._coremidi.MIDIEntityGetDestination(entity, k)
                    ep_name = cm.get_endpoint_name(ep)
                    client.add_port(ep, ep_name, self.Client.Port.CAP_WRITE)
            self._clients[name] = client

    def __iter__(self):
        return iter(self._clients.values())

    def __len__(self) -> int:
        return len(self._clients)

    def get_client(self, key: str) -> SequencerHardware.Client:
        return self._clients[key]
    __getitem__ = get_client

    def get_client_and_port(self, cname: str, pname: str) -> tuple[int, int]:
        client = self[cname]
        port = client[pname]
        return (client.client, port.port)

    def __str__(self) -> str:
        retstr = ''
        for client in self:
            retstr += str(client)
        return retstr


def _build_midi_bytes(event: midi.Event) -> bytes | None:
    """Convert a midi Event to raw MIDI bytes for CoreMIDI."""
    if isinstance(event, midi.EndOfTrackEvent):
        return None
    if isinstance(event, midi.NoteOnEvent):
        return bytes([0x90 | event.channel, event.pitch, event.velocity])
    if isinstance(event, midi.NoteOffEvent):
        return bytes([0x80 | event.channel, event.pitch, event.velocity])
    if isinstance(event, midi.ControlChangeEvent):
        return bytes([0xB0 | event.channel, event.control, event.value])
    if isinstance(event, midi.ProgramChangeEvent):
        return bytes([0xC0 | event.channel, event.value])
    if isinstance(event, midi.ChannelAfterTouchEvent):
        return bytes([0xD0 | event.channel, event.value])
    if isinstance(event, midi.PitchWheelEvent):
        value = event.pitch + 0x2000
        return bytes([0xE0 | event.channel, value & 0x7F, (value >> 7) & 0x7F])
    if isinstance(event, midi.AfterTouchEvent):
        return bytes([0xA0 | event.channel, event.pitch, event.value])
    return None


def _parse_midi_bytes(data: bytes, timestamp: int) -> midi.Event | None:
    """Parse raw MIDI bytes into a midi Event."""
    if not data:
        return None
    status = data[0]
    channel = status & 0x0F
    msg_type = status & 0xF0
    if msg_type == 0x90 and len(data) >= 3:
        ev = midi.NoteOnEvent(channel=channel)
        ev.pitch = data[1]
        ev.velocity = data[2]
        return ev
    if msg_type == 0x80 and len(data) >= 3:
        ev = midi.NoteOffEvent(channel=channel)
        ev.pitch = data[1]
        ev.velocity = data[2]
        return ev
    if msg_type == 0xB0 and len(data) >= 3:
        ev = midi.ControlChangeEvent(channel=channel)
        ev.control = data[1]
        ev.value = data[2]
        return ev
    if msg_type == 0xC0 and len(data) >= 2:
        ev = midi.ProgramChangeEvent(channel=channel)
        ev.value = data[1]
        return ev
    if msg_type == 0xD0 and len(data) >= 2:
        ev = midi.ChannelAfterTouchEvent(channel=channel)
        ev.value = data[1]
        return ev
    if msg_type == 0xE0 and len(data) >= 3:
        ev = midi.PitchWheelEvent(channel=channel)
        ev.data[0] = data[1]
        ev.data[1] = data[2]
        return ev
    return None


class SequencerWrite(Sequencer):
    """Schedule MIDI output with tick-accurate timestamps via CoreMIDI."""

    def __init__(self, **kw) -> None:
        super().__init__(**kw)
        self._output_port = cm.midi_output_port_create(self._client, "output")
        self._dest_endpoint = None

    def subscribe_port(self, client: int, port: int) -> None:
        """Subscribe to a destination endpoint for writing.

        For CoreMIDI, `port` is the MIDIEndpointRef of the destination.
        `client` is ignored (kept for API compatibility with ALSA).
        """
        self._dest_endpoint = cm.MIDIEndpointRef(int(port))

    def subscribe_port_by_index(self, index: int) -> None:
        """Subscribe to a destination by its index in the system destination list."""
        self._dest_endpoint = cm.get_destination(index)

    # CoreMIDI has no output buffer in the ALSA sense; report a large
    # value so callers that throttle based on remaining buffer space
    # (e.g. ``if buf < 1000: time.sleep(.5)``) never stall.
    OUTPUT_BUFFER_SIZE: int = 65536

    def event_write(self, event: midi.Event, direct: bool = False,
                    relative: bool = False, tick: bool = False) -> int | None:
        if isinstance(event, midi.EndOfTrackEvent):
            return None
        if self._dest_endpoint is None:
            raise RuntimeError("No destination subscribed")

        # Tempo changes update internal state (no MIDI bytes to send)
        if isinstance(event, midi.SetTempoEvent):
            self.change_tempo(int(event.bpm))
            return self.OUTPUT_BUFFER_SIZE

        midi_bytes = _build_midi_bytes(event)
        if midi_bytes is None:
            return None

        # Calculate timestamp
        if direct:
            timestamp = 0  # immediate
        elif tick:
            timestamp = self._tick_to_host_time(event.tick)
        else:
            # msdelay-based scheduling
            ms = getattr(event, 'msdelay', 0)
            nanos = int(ms * 1_000_000)
            timestamp = self._start_host_time + cm.nanos_to_host_time(nanos)

        # Build and send packet
        pktlist = cm.MIDIPacketList()
        pkt = cm.packet_list_init(pktlist)
        pkt = cm.packet_list_add(pktlist, pkt, timestamp, midi_bytes)
        cm.midi_send(self._output_port, self._dest_endpoint, pktlist)
        return self.OUTPUT_BUFFER_SIZE


class SequencerRead(Sequencer):
    """Subscribe to MIDI input and read events."""

    def __init__(self, **kw) -> None:
        super().__init__(**kw)
        self._lock = threading.Lock()

        # Must keep a reference to the callback to prevent GC
        self._read_proc = cm.MIDIReadProc(self._on_read)
        self._input_port = cm.midi_input_port_create(
            self._client, "input", self._read_proc)

    def _on_read(self, pktlist_ptr, read_proc_ref_con, src_conn_ref_con) -> None:
        """Callback invoked by CoreMIDI on a separate thread."""
        pktlist = pktlist_ptr.contents
        for timestamp, data in cm.iter_packets(pktlist):
            ev = _parse_midi_bytes(data, timestamp)
            if ev is not None:
                if self._queue_running and self._start_host_time > 0:
                    ev.tick = self._host_time_to_tick(timestamp)
                with self._lock:
                    self._read_queue.append(ev)

    def subscribe_port(self, client: int, port: int) -> None:
        """Subscribe to a source endpoint for reading.

        For CoreMIDI, `port` is the MIDIEndpointRef of the source.
        `client` is ignored (kept for API compatibility with ALSA).
        """
        source = cm.MIDIEndpointRef(int(port))
        cm.midi_port_connect_source(self._input_port, source)
        self._source_endpoint = source

    def subscribe_port_by_index(self, index: int) -> None:
        """Subscribe to a source by its index in the system source list."""
        source = cm.get_source(index)
        cm.midi_port_connect_source(self._input_port, source)
        self._source_endpoint = source

    def event_read(self) -> midi.Event | None:
        with self._lock:
            if self._read_queue:
                return self._read_queue.popleft()
        return None


class SequencerDuplex(Sequencer):
    """Both read and write MIDI events."""

    def __init__(self, **kw) -> None:
        super().__init__(**kw)
        self._lock = threading.Lock()
        self._read_queue: deque[midi.Event] = deque()
        self._read_proc = cm.MIDIReadProc(self._on_read)
        self._output_port = cm.midi_output_port_create(self._client, "output")
        self._input_port = cm.midi_input_port_create(
            self._client, "input", self._read_proc)
        self._dest_endpoint = None
        self._source_endpoint = None

    def _on_read(self, pktlist_ptr, read_proc_ref_con, src_conn_ref_con) -> None:
        pktlist = pktlist_ptr.contents
        for timestamp, data in cm.iter_packets(pktlist):
            ev = _parse_midi_bytes(data, timestamp)
            if ev is not None:
                if self._queue_running and self._start_host_time > 0:
                    ev.tick = self._host_time_to_tick(timestamp)
                with self._lock:
                    self._read_queue.append(ev)

    def subscribe_read_port(self, client: int, port: int) -> None:
        source = cm.MIDIEndpointRef(int(port))
        cm.midi_port_connect_source(self._input_port, source)
        self._source_endpoint = source

    def subscribe_write_port(self, client: int, port: int) -> None:
        self._dest_endpoint = cm.MIDIEndpointRef(int(port))

    def subscribe_port(self, client: int, port: int) -> None:
        self.subscribe_write_port(client, port)

    OUTPUT_BUFFER_SIZE: int = 65536

    def event_write(self, event: midi.Event, direct: bool = False,
                    relative: bool = False, tick: bool = False) -> int | None:
        if isinstance(event, midi.EndOfTrackEvent):
            return None
        if self._dest_endpoint is None:
            raise RuntimeError("No destination subscribed")
        if isinstance(event, midi.SetTempoEvent):
            self.change_tempo(int(event.bpm))
            return self.OUTPUT_BUFFER_SIZE
        midi_bytes = _build_midi_bytes(event)
        if midi_bytes is None:
            return None
        if direct:
            timestamp = 0
        elif tick:
            timestamp = self._tick_to_host_time(event.tick)
        else:
            ms = getattr(event, 'msdelay', 0)
            nanos = int(ms * 1_000_000)
            timestamp = self._start_host_time + cm.nanos_to_host_time(nanos)
        pktlist = cm.MIDIPacketList()
        pkt = cm.packet_list_init(pktlist)
        pkt = cm.packet_list_add(pktlist, pkt, timestamp, midi_bytes)
        cm.midi_send(self._output_port, self._dest_endpoint, pktlist)
        return self.OUTPUT_BUFFER_SIZE

    def event_read(self) -> midi.Event | None:
        with self._lock:
            if self._read_queue:
                return self._read_queue.popleft()
        return None
