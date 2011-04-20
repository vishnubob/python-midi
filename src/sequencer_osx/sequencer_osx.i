%module sequencer_osx
%feature("typemaps");
%feature("newobject");

%{
#include <CoreFoundation/CoreFoundation.h>
#include <CoreMIDI/CoreMIDI.h>

/* MIDIClientCreate */
MIDIClientRef _MIDIClientCreate(CFStringRef clientName)
{
    OSStatus err;
    MIDIClientRef client;

    /* create client handle */
    err = MIDIClientCreate(clientName, NULL, NULL, &client);
    if(err != noErr)
    {
        PyErr_SetString(PyExc_SystemError, "Error during MIDIClientCreate.");
        return 0;
    }
    return client;
}

/* MIDIClientDispose */
void _MIDIClientDispose(MIDIClientRef client)
{
    OSStatus err;
    err = MIDIClientDispose(client);
    if(err != noErr)
    {
        PyErr_SetString(PyExc_SystemError, "Error during MIDIClientDispose.");
    }
}

/* MIDISourceCreate */
MIDIEndpointRef _MIDISourceCreate(MIDIClientRef client, CFStringRef sourceName)
{
    OSStatus err;
    MIDIEndpointRef outSrc;
    err = MIDISourceCreate(client, sourceName, &outSrc);
    if(err != noErr)
    {
        PyErr_SetString(PyExc_SystemError, "Error during MIDISourceCreate.");
        return 0;
    }
    return outSrc;
}

/* MIDIOutputPortCreate */
MIDIPortRef _MIDIOutputPortCreate(MIDIClientRef client, CFStringRef portName)
{
    OSStatus err;
    MIDIPortRef outPort;
    err = MIDIOutputPortCreate(client, portName, &outPort);
    if(err != noErr)
    {
        PyErr_SetString(PyExc_SystemError, "Error during MIDIOutputPortCreate.");
        return 0;
    }
    return outPort;
}

/* MIDIPortConnectSource */
void _MIDIPortConnectSource(MIDIPortRef port, MIDIEndpointRef endpoint)
{
    OSStatus err;
    MIDIPortRef outPort;
    err = MIDIPortConnectSource(port, endpoint, NULL);
    if(err != noErr)
    {
        PyErr_SetString(PyExc_SystemError, "Error during MIDIPortConnectSource.");
    }
}

/*
void _MIDISend(MIDIEndpointRef *midi_source, unsigned char val)
{
    MIDIPacketList pktlist;
    MIDIPacket p;
    Byte data[3];
    p_head = MIDIPacketListInit(&pktlist);
    data[0] = 176; // Control change
    data[1] = 1; // Modulation
    data[2] = val; // Value
    MIDIPacketListAdd( &pktlist, sizeof(p), p_head, 0, 3, data);
    MIDIReceived(*midi_source, &pktlist);
}
*/



/* MIDIGetNumberOfDevices */
unsigned long _MIDIGetNumberOfDevices()
{
    return (unsigned long) MIDIGetNumberOfDevices();
}

%}

%typemap(in) CFStringRef 
{
    if (!PyString_Check($input)) 
    {
        PyErr_SetString(PyExc_ValueError, "Expecting a string");
        return NULL;
    }
    $1 = CFStringCreateWithCString(NULL, PyString_AsString($input), kCFStringEncodingASCII);
}

%typemap(freearg) MIDIClientRef* 
{
    OSStatus err;
    err = MIDIClientDispose($1);
    if(err != noErr)
    {
        PyErr_SetString(PyExc_SystemError, "Error during MIDIClientDispose.");
    }
}

%typemap(freearg) CFStringRef 
{
    CFRelease($1);
}

%typemap(arginit) CFStringRef 
{
    $1 = NULL;
}

%typemap(out) CFStringRef 
{
    unsigned int len = CFStringGetLength($1);
    char *buffer = malloc(len + 1);
    if (CFStringGetCString($1, buffer, len + 1, kCFStringEncodingASCII)) 
    {
        $result = PyString_FromStringAndSize(buffer, len);
        free(buffer);
        CFRelease($1);
    } else 
    {
        PyErr_SetString(PyExc_ValueError, "Can't convert string");
        CFRelease($1);
        return NULL;
    }
}

unsigned long _MIDIGetNumberOfDevices();
MIDIClientRef _MIDIClientCreate(CFStringRef clientName);
void _MIDIClientDispose(MIDIClientRef client);
MIDIEndpointRef _MIDISourceCreate(MIDIClientRef client, CFStringRef sourceName);
MIDIPortRef _MIDIOutputPortCreate(MIDIClientRef client, CFStringRef portName);
void _MIDIPortConnectSource(MIDIPortRef port, MIDIEndpointRef endpoint);

