import sequencer_osx
print "MIDIGetNumberOfDevices:", sequencer_osx._MIDIGetNumberOfDevices()
client = sequencer_osx._MIDIClientCreate("python")
endpoint = sequencer_osx._MIDISourceCreate(client, "python-source")
port = sequencer_osx._MIDIOutputPortCreate(client, "python-port")
sequencer_osx._MIDIPortConnectSource(port, endpoint)
print client, endpoint, endpoint
raw_input()
#sequencer_osx._MIDIClientDispose(handle)
