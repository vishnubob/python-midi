%module sequencer_osx
%feature("typemaps");
%feature("newobject");

%{
#include <CoreFoundation/CoreFoundation.h>
#include <CoreMIDI/CoreMIDI.h>

/* MIDIClientCreate */
MIDIClientRef *_MIDIClientCreate(const char *cName)
{
    OSStatus err;
    CFStringRef ClientName;
    MIDIClientRef *client;

    /* allocate client handle */
    client = (MIDIClientRef *)malloc(sizeof(MIDIClientRef));
    if(!client)
    {
        PyErr_SetString(PyExc_SystemError, "Expecting a string");
        return NULL;
    }

    /* create client handle */
    ClientName = CFStringCreateWithCString(NULL, cName, kCFStringEncodingASCII);
    err = MIDIClientCreate(ClientName, NULL, NULL, client);
    if(err != noErr)
    {
        PyErr_SetString(PyExc_SystemError, "Error during MIDIClientCreate.");
        return NULL;
    }
    return client;
}

/* MIDIClientDispose */
void _MIDIClientDispose(MIDIClientRef *client)
{
    OSStatus err;
    err = MIDIClientDispose(*client);
    free(client);
    if(err != noErr)
    {
        PyErr_SetString(PyExc_SystemError, "Error during MIDIClientDispose..");
    }
}

/* MIDISourceCreate */
MIDIEndpointRef *_MIDISourceCreate(MIDIClientRef *client, CFStringRef name)
{
    OSStatus err;
    CFStringRef ClientName;

    /* allocate client handle */
    MIDIClientRef *client = (MIDIClientRef *)malloc(sizeof(MIDIClientRef));
    if(!client)
    {
        PyErr_SetString(PyExc_SystemError, "Expecting a string");
        return NULL;
    }

    MIDISourceCreate(*client,
    MIDIClientRef client, CFStringRef name, MIDIEndpointRef * outSrc );

    /* create client handle */
    ClientName = CFStringCreateWithCString(NULL, cName, kCFStringEncodingASCII);
    err = MIDIClientCreate(ClientName, NULL, NULL, client);
    if(err != noErr)
    {
        PyErr_SetString(PyExc_SystemError, "Error during MIDIClientCreate.");
        return NULL;
    }
    return client;
}

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
MIDIClientRef *_MIDIClientCreate(const char *cName);
void _MIDIClientDispose(MIDIClientRef *client);

