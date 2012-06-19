import select
import sequencer_alsa as S
import midi

__SWIG_NS_SET__ = set(['__class__', '__del__', '__delattr__', '__dict__', '__doc__', '__getattr__', '__getattribute__', '__hash__', '__init__', '__module__', '__new__', '__reduce__', '__reduce_ex__', '__repr__', '__setattr__', '__str__', '__swig_getmethods__', '__swig_setmethods__', '__weakref__', 'this', 'thisown'])

def stringify(name, obj, indent=0):
    retstr = ''
    datafields = False
    if getattr(obj, 'this', False):
        datafields = dir(obj)
        # filter unwanted names
        datafields = list(set(datafields) - __SWIG_NS_SET__)
        retstr += '%s%s ::\n' % ('    ' * indent, name)
        for key in datafields:
            value = getattr(obj, key, "n/a")
            retstr += stringify(key, value, indent+1)
    else:
        retstr += '%s%s: %s\n' % ('    ' * indent, name, obj)
    return retstr

class Sequencer(object):
    __ARGUMENTS__ = {
        'alsa_sequencer_name':'__sequencer__',
        'alsa_sequencer_stream':S.SND_SEQ_OPEN_DUPLEX,
        'alsa_sequencer_mode':S.SND_SEQ_NONBLOCK,
        'alsa_sequencer_type':'default',
        'alsa_port_name':'__port__',
        'alsa_port_caps':S.SND_SEQ_PORT_CAP_READ,
        'alsa_port_type':S.SND_SEQ_PORT_TYPE_MIDI_GENERIC,
        'alsa_queue_name':'__queue__',
        'sequencer_tempo':120,
        'sequencer_resolution':1000,
    }
    DefaultArguments = {}

    def __init__(self, **ns):
        # seed with baseline arguments
        self.__dict__.update(self.__ARGUMENTS__)
        # update with default arguments from concrete class
        self.__dict__.update(self.DefaultArguments)
        # apply user arguments
        self.__dict__.update(ns)
        self.client = None
        self._queue_running = False
        self._poll_descriptors = []
        self.init()

    def __del__(self):
        if self.client:
            S.snd_seq_close(self.client)

    def init(self):
        self._init_handle()
        self._init_port()
        self._init_queue()

    def set_nonblock(self, nonblock=True):
        if nonblock:
            self.alsa_sequencer_mode = S.SND_SEQ_NONBLOCK
        else:
            self.alsa_sequencer_mode = 0
        S.snd_seq_nonblock(self.client, self.alsa_sequencer_mode)

    def get_nonblock(self):
        if self.alsa_sequencer_mode == S.SND_SEQ_NONBLOCK:
            return True
        else:
            return False

    def _error(self, errcode):
        strerr = S.snd_strerror(errcode)
        msg = "ALSAError[%d]: %s" % (errcode, strerr)
        raise RuntimeError, msg

    def _init_handle(self):
        ret = S.open_client(self.alsa_sequencer_name,
                            self.alsa_sequencer_type,
                            self.alsa_sequencer_stream,
                            self.alsa_sequencer_mode)
        if ret == None:
            # XXX: global error
            self._error(ret)
        self.client = ret
        self.client_id = S.snd_seq_client_id(self.client)
        self.output_buffer_size = S.snd_seq_get_output_buffer_size(self.client)
        self.input_buffer_size = S.snd_seq_get_input_buffer_size(self.client)
        self._set_poll_descriptors()

    def _init_port(self):
        err = S.snd_seq_create_simple_port(self.client,
                                            self.alsa_port_name, 
                                            self.alsa_port_caps, 
                                            self.alsa_port_type)
        if err < 0: self._error(err)
        self.port = err

    def _new_subscribe(self, sender, dest, read=True):
        subscribe = S.new_port_subscribe()
        if read:
            self.read_sender = sender
            self.read_dest = dest
            S.snd_seq_port_subscribe_set_sender(subscribe, self.read_sender)
            S.snd_seq_port_subscribe_set_dest(subscribe, self.read_dest)
        else:
            self.write_sender = sender
            self.write_dest = dest
            S.snd_seq_port_subscribe_set_sender(subscribe, self.write_sender)
            S.snd_seq_port_subscribe_set_dest(subscribe, self.write_dest)
        S.snd_seq_port_subscribe_set_queue(subscribe, self.queue)
        return subscribe

    def _subscribe_port(self, subscribe):
        err = S.snd_seq_subscribe_port(self.client, subscribe)
        if err < 0: self._error(err)

    def _my_address(self):
        addr = S.snd_seq_addr_t()
        addr.client = self.client_id
        addr.port = self.port
        return addr

    def _new_address(self, client, port):
        addr = S.snd_seq_addr_t()
        addr.client = int(client)
        addr.port = int(port)
        return addr
    
    def _init_queue(self):
        err = S.snd_seq_alloc_named_queue(self.client, self.alsa_queue_name)
        if err < 0: self._error(err)
        self.queue = err
        adjtempo = int(60.0 * 1000000.0 / self.sequencer_tempo)
        S.init_queue_tempo(self.client, self.queue, 
                            adjtempo, self.sequencer_resolution)

    def _control_queue(self, ctype, cvalue, event=None):
        err = S.snd_seq_control_queue(self.client, self.queue, ctype, cvalue, event)
        if err < 0: self._error(err)
        self.drain()

    def _set_event_broadcast(self, event):
        event.source.client = source.client
        event.source.port = source.port
        event.dest.client = S.SND_SEQ_ADDRESS_SUBSCRIBERS
        event.dest.port = S.SND_SEQ_ADDRESS_UNKNOWN

    def queue_get_tick_time(self):
        status = S.new_queue_status(self.client, self.queue)
        S.snd_seq_get_queue_status(self.client, self.queue, status)
        res = S.snd_seq_queue_status_get_tick_time(status)
        S.free_queue_status(status)
        return res

    def queue_get_real_time(self):
        status = S.new_queue_status(self.client, self.queue)
        S.snd_seq_get_queue_status(self.client, self.queue, status)
        res = S.snd_seq_queue_status_get_real_time(status)
        S.free_queue_status(status)
        return (res.tv_sec, res.tv_nsec)

    def change_tempo(self, tempo, event=None):
        adjbpm = int(60.0 * 1000000.0 / tempo)
        self._control_queue(S.SND_SEQ_EVENT_TEMPO, adjbpm, event)
        self.sequencer_tempo = tempo
        return True

    def start_sequencer(self, event=None):
        if not self._queue_running:
            self._control_queue(S.SND_SEQ_EVENT_START, 0, event)
            self._queue_running = True

    def continue_sequencer(self, event=None):
        if not self._queue_running:
            self._control_queue(S.SND_SEQ_EVENT_CONTINUE, 0, event)
            self._queue_running = True

    def stop_sequencer(self, event=None):
        if self._queue_running:
            self._control_queue(S.SND_SEQ_EVENT_STOP, 0, event)
            self._queue_running = False
    
    def drain(self):
        S.snd_seq_drain_output(self.client)

    def queue_eventlen(self):
        status = S.new_queue_status(self.client, self.queue)
        S.snd_seq_queue_status_get_events(status)

    def _set_poll_descriptors(self):
        self._poll_descriptors = S.client_poll_descriptors(self.client)

    def configure_poll(self, poll):
        for fd in self._poll_descriptors:
            poll.register(fd, select.POLLIN)

    def drop_output(self):
        S.snd_seq_drop_output_buffer(self.client)

    def output_pending(self):
        return S.snd_seq_event_output_pending(self.client)

    ## EVENT HANDLERS
    ##
    def event_write(self, event, direct=False, relative=False, tick=False):
        #print event.__class__, event
        ## Event Filter
        if isinstance(event, midi.EndOfTrackEvent):
            return
        seqev = S.snd_seq_event_t()
        ## common
        seqev.dest.client = self.write_dest.client
        seqev.dest.port = self.write_dest.port
        seqev.source.client = self.write_sender.client
        seqev.source.port = self.write_sender.port
        if direct:
            # no scheduling
            seqev.queue = S.SND_SEQ_QUEUE_DIRECT
        else:
            seqev.queue = self.queue
            seqev.flags &= (S.SND_SEQ_TIME_STAMP_MASK|S.SND_SEQ_TIME_MODE_MASK)
            if relative:
                seqev.flags |= S.SND_SEQ_TIME_MODE_REL
            else:
                seqev.flags |= S.SND_SEQ_TIME_MODE_ABS
            if tick:
                seqev.flags |= S.SND_SEQ_TIME_STAMP_TICK
                seqev.time.tick = event.tick
            else:
                seqev.flags |= S.SND_SEQ_TIME_STAMP_REAL
                sec = int(event.msdelay / 1000)
                nsec = int((event.msdelay - (sec * 1000)) * 1000000)
                seqev.time.time.tv_sec = sec
                seqev.time.time.tv_nsec = nsec

        ## Tempo Change
        if isinstance(event, midi.SetTempoEvent):
            adjtempo = int(60.0 * 1000000.0 / event.bpm)
            seqev.type = S.SND_SEQ_EVENT_TEMPO
            seqev.dest.client = S.SND_SEQ_CLIENT_SYSTEM
            seqev.dest.port = S.SND_SEQ_PORT_SYSTEM_TIMER
            seqev.data.queue.queue = self.queue
            seqev.data.queue.param.value = adjtempo
        ## Note Event
        elif isinstance(event, midi.NoteEvent):
            if isinstance(event, midi.NoteOnEvent):
                seqev.type = S.SND_SEQ_EVENT_NOTEON
            if isinstance(event, midi.NoteOffEvent):
                seqev.type = S.SND_SEQ_EVENT_NOTEOFF
            seqev.data.note.channel = event.channel
            seqev.data.note.note = event.pitch
            seqev.data.note.velocity = event.velocity
        ## Control Change
        elif isinstance(event, midi.ControlChangeEvent):
            seqev.type = S.SND_SEQ_EVENT_CONTROLLER
            seqev.data.control.channel = event.channel
            seqev.data.control.param = event.control
            seqev.data.control.value = event.value
        ## Program Change
        elif isinstance(event, midi.ProgramChangeEvent):
            seqev.type = S.SND_SEQ_EVENT_PGMCHANGE
            seqev.data.control.channel = event.channel
            seqev.data.control.value = event.value
        ## Pitch Bench
        elif isinstance(event, midi.PitchWheelEvent):
            seqev.type = S.SND_SEQ_EVENT_PITCHBEND
            seqev.data.control.channel = event.channel
            seqev.data.control.value = event.pitch
        ## Unknown
        else:
            print "Warning :: Unknown event type: %s" % event
            return None
            
        err = S.snd_seq_event_output(self.client, seqev)
        if (err < 0): self._error(err)
        self.drain()
        return self.output_buffer_size - err

    def event_read(self):
        ev = S.event_input(self.client)
        if ev and (ev < 0): self._error(ev)
        if ev and ev.type in (S.SND_SEQ_EVENT_NOTEON, S.SND_SEQ_EVENT_NOTEOFF):
            if ev.type == S.SND_SEQ_EVENT_NOTEON:
                mev = midi.NoteOnEvent()
                mev.channel = ev.data.note.channel
                mev.pitch = ev.data.note.note
                mev.velocity = ev.data.note.velocity
            elif ev.type == S.SND_SEQ_EVENT_NOTEOFF:
                mev = midi.NoteOffEvent()
                mev.channel = ev.data.note.channel
                mev.pitch = ev.data.note.note
                mev.velocity = ev.data.note.velocity
            if ev.time.time.tv_nsec:
                # convert to ms
                mev.msdeay = \
                    (ev.time.time.tv_nsec / 1e6) + (ev.time.time.tv_sec * 1e3)
            else:
                mev.tick = ev.time.tick
            return mev
        else:
            return None

class SequencerHardware(Sequencer):
    SequencerName = "__hw__"
    SequencerStream = S.SND_SEQ_OPEN_DUPLEX
    SequencerType = "hw"
    SequencerMode = 0

    class Client(object):
        def __init__(self, client, name):
            self.client = client
            self.name = name
            self._ports = {}

        def __str__(self):
            retstr = '] client(%d) "%s"\n' % (self.client, self.name)
            for port in self:
                retstr += str(port)
            return retstr

        def add_port(self, port, name, caps):
            port = self.Port(port, name, caps)
            self._ports[name] = port

        def __iter__(self):
            return self._ports.itervalues()

        def __len__(self):
            return len(self._ports)

        def get_port(self, key):
            return self._ports[key]
        __getitem__ = get_port
        
        class Port(object):
            def __init__(self, port, name, caps):
                self.port = port
                self.name = name
                self.caps = caps
                self.caps_read = self.caps & S.SND_SEQ_PORT_CAP_READ
                self.caps_write = self.caps & S.SND_SEQ_PORT_CAP_WRITE
                self.caps_subs_read = self.caps & S.SND_SEQ_PORT_CAP_SUBS_READ
                self.caps_subs_write = self.caps & S.SND_SEQ_PORT_CAP_SUBS_WRITE

            def __str__(self):
                flags = []
                if self.caps_read: flags.append('r')
                if self.caps_write: flags.append('w')
                if self.caps_subs_read: flags.append('sender')
                if self.caps_subs_write: flags.append('receiver')
                flags = str.join(', ', flags)
                retstr = ']   port(%d) [%s] "%s"\n' % (self.port, flags, self.name)
                return retstr


    def init(self):
        self._clients = {}
        self._init_handle()
        self._query_clients()

    def __iter__(self):
        return self._clients.itervalues()

    def __len__(self):
        return len(self._clients)

    def get_client(self, key):
        return self._clients[key]
    __getitem__ = get_client

    def get_client_and_port(self, cname, pname):
        client = self[cname]
        port = client[pname]
        return (client.client, port.port)

    def __str__(self):
        retstr = ''
        for client in self:
            retstr += str(client)
        return retstr

    def _query_clients(self):
        self._clients = {}
        S.snd_seq_drop_output(self.client)
        cinfo = S.new_client_info()
        pinfo = S.new_port_info()
        S.snd_seq_client_info_set_client(cinfo, -1)
        # for each client
        while S.snd_seq_query_next_client(self.client, cinfo) >= 0:
            client = S.snd_seq_client_info_get_client(cinfo)
            cname = S.snd_seq_client_info_get_name(cinfo)
            cobj = self.Client(client, cname)
            self._clients[cname] = cobj
            # get port data
            S.snd_seq_port_info_set_client(pinfo, client)
            S.snd_seq_port_info_set_port(pinfo, -1)
            while (S.snd_seq_query_next_port(self.client, pinfo) >= 0):
                cap = S.snd_seq_port_info_get_capability(pinfo)
                client = S.snd_seq_port_info_get_client(pinfo)
                port = S.snd_seq_port_info_get_port(pinfo)
                pname = S.snd_seq_port_info_get_name(pinfo)
                cobj.add_port(port, pname, cap)

class SequencerRead(Sequencer):
    DefaultArguments = {
      'sequencer_name':'__SequencerRead__',
      'sequencer_stream':not S.SND_SEQ_NONBLOCK,
      'alsa_port_caps':S.SND_SEQ_PORT_CAP_WRITE | S.SND_SEQ_PORT_CAP_SUBS_WRITE,
    }

    def subscribe_port(self, client, port):
        sender = self._new_address(client, port)
        dest = self._my_address()
        subscribe = self._new_subscribe(sender, dest, read=True)
        S.snd_seq_port_subscribe_set_time_update(subscribe, True)
        #S.snd_seq_port_subscribe_set_time_real(subscribe, True)
        self._subscribe_port(subscribe)

class SequencerWrite(Sequencer):
    DefaultArguments = {
      'sequencer_name':'__SequencerWrite__',
      'sequencer_stream':not S.SND_SEQ_NONBLOCK,
      'alsa_port_caps':S.SND_SEQ_PORT_CAP_READ | S.SND_SEQ_PORT_CAP_SUBS_READ
    }

    def subscribe_port(self, client, port):
        sender = self._my_address()
        dest = self._new_address(client, port)
        subscribe = self._new_subscribe(sender, dest, read=False)
        self._subscribe_port(subscribe)

class SequencerDuplex(Sequencer):
    DefaultArguments = {
      'sequencer_name':'__SequencerWrite__',
      'sequencer_stream':not S.SND_SEQ_NONBLOCK,
      'alsa_port_caps':S.SND_SEQ_PORT_CAP_READ | S.SND_SEQ_PORT_CAP_SUBS_READ |
                      S.SND_SEQ_PORT_CAP_WRITE | S.SND_SEQ_PORT_CAP_SUBS_WRITE
    }

    def subscribe_read_port(self, client, port):
        sender = self._new_address(client, port)
        dest = self._my_address()
        subscribe = self._new_subscribe(sender, dest, read=True)
        S.snd_seq_port_subscribe_set_time_update(subscribe, True)
        #S.snd_seq_port_subscribe_set_time_real(subscribe, True)
        self._subscribe_port(subscribe)

    def subscribe_write_port(self, client, port):
        sender = self._my_address()
        dest = self._new_address(client, port)
        subscribe = self._new_subscribe(sender, dest, read=False)
        self._subscribe_port(subscribe)

