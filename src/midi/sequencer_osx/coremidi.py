"""Low-level ctypes bindings to macOS CoreMIDI and related frameworks."""
from __future__ import annotations

import ctypes
import ctypes.util
from ctypes import (
    c_void_p, c_int32, c_uint32, c_uint64, c_uint16, c_uint8,
    c_char_p, c_bool, byref, POINTER, Structure, CFUNCTYPE,
)

# --- Load frameworks ---

_coremidi = ctypes.cdll.LoadLibrary(
    '/System/Library/Frameworks/CoreMIDI.framework/CoreMIDI')
_audio_toolbox = ctypes.cdll.LoadLibrary(
    '/System/Library/Frameworks/AudioToolbox.framework/AudioToolbox')
_core_foundation = ctypes.cdll.LoadLibrary(
    '/System/Library/Frameworks/CoreFoundation.framework/CoreFoundation')

# --- Type aliases ---

OSStatus = c_int32
MIDIObjectRef = c_uint32
MIDIClientRef = MIDIObjectRef
MIDIPortRef = MIDIObjectRef
MIDIEndpointRef = MIDIObjectRef
MIDIDeviceRef = MIDIObjectRef
MIDIEntityRef = MIDIObjectRef
MIDITimeStamp = c_uint64
CFStringRef = c_void_p
CFStringEncoding = c_uint32
ItemCount = c_uint32

kCFStringEncodingUTF8 = 0x08000100
kMIDIPropertyName = ctypes.c_char_p(b"name")


# --- MIDIPacket / MIDIPacketList structures ---

class MIDIPacket(Structure):
    _pack_ = 1
    _fields_ = [
        ('timeStamp', MIDITimeStamp),
        ('length', c_uint16),
        ('data', c_uint8 * 256),
    ]


class MIDIPacketList(Structure):
    _pack_ = 1
    _fields_ = [
        ('numPackets', c_uint32),
        ('packet', MIDIPacket * 1),
    ]


# --- Read proc callback type ---
# void (*MIDIReadProc)(const MIDIPacketList *pktlist, void *readProcRefCon, void *srcConnRefCon)
MIDIReadProc = CFUNCTYPE(None, POINTER(MIDIPacketList), c_void_p, c_void_p)

# --- CoreFoundation string helpers ---

_core_foundation.CFStringCreateWithCString.restype = CFStringRef
_core_foundation.CFStringCreateWithCString.argtypes = [c_void_p, c_char_p, CFStringEncoding]

_core_foundation.CFStringGetLength.restype = c_int32
_core_foundation.CFStringGetLength.argtypes = [CFStringRef]

_core_foundation.CFStringGetCString.restype = c_bool
_core_foundation.CFStringGetCString.argtypes = [CFStringRef, c_char_p, c_int32, CFStringEncoding]

_core_foundation.CFRelease.restype = None
_core_foundation.CFRelease.argtypes = [c_void_p]


def cfstring_create(s: str) -> CFStringRef:
    return _core_foundation.CFStringCreateWithCString(
        None, s.encode('utf-8'), kCFStringEncodingUTF8)


def cfstring_to_str(cfstr: CFStringRef) -> str:
    length = _core_foundation.CFStringGetLength(cfstr)
    buf_size = length * 4 + 1
    buf = ctypes.create_string_buffer(buf_size)
    if _core_foundation.CFStringGetCString(cfstr, buf, buf_size, kCFStringEncodingUTF8):
        return buf.value.decode('utf-8')
    return ''


def cfrelease(ref: c_void_p) -> None:
    if ref:
        _core_foundation.CFRelease(ref)


# --- MIDIClient lifecycle ---

_coremidi.MIDIClientCreate.restype = OSStatus
_coremidi.MIDIClientCreate.argtypes = [CFStringRef, c_void_p, c_void_p, POINTER(MIDIClientRef)]

_coremidi.MIDIClientDispose.restype = OSStatus
_coremidi.MIDIClientDispose.argtypes = [MIDIClientRef]


def midi_client_create(name: str) -> MIDIClientRef:
    client = MIDIClientRef()
    cfname = cfstring_create(name)
    status = _coremidi.MIDIClientCreate(cfname, None, None, byref(client))
    cfrelease(cfname)
    if status != 0:
        raise OSError(f"MIDIClientCreate failed with status {status}")
    return client


def midi_client_dispose(client: MIDIClientRef) -> None:
    _coremidi.MIDIClientDispose(client)


# --- Ports ---

_coremidi.MIDIOutputPortCreate.restype = OSStatus
_coremidi.MIDIOutputPortCreate.argtypes = [MIDIClientRef, CFStringRef, POINTER(MIDIPortRef)]

_coremidi.MIDIInputPortCreate.restype = OSStatus
_coremidi.MIDIInputPortCreate.argtypes = [MIDIClientRef, CFStringRef, MIDIReadProc, c_void_p, POINTER(MIDIPortRef)]


def midi_output_port_create(client: MIDIClientRef, name: str) -> MIDIPortRef:
    port = MIDIPortRef()
    cfname = cfstring_create(name)
    status = _coremidi.MIDIOutputPortCreate(client, cfname, byref(port))
    cfrelease(cfname)
    if status != 0:
        raise OSError(f"MIDIOutputPortCreate failed with status {status}")
    return port


def midi_input_port_create(client: MIDIClientRef, name: str,
                           read_proc: MIDIReadProc) -> MIDIPortRef:
    port = MIDIPortRef()
    cfname = cfstring_create(name)
    status = _coremidi.MIDIInputPortCreate(client, cfname, read_proc, None, byref(port))
    cfrelease(cfname)
    if status != 0:
        raise OSError(f"MIDIInputPortCreate failed with status {status}")
    return port


# --- Virtual endpoints ---

_coremidi.MIDISourceCreate.restype = OSStatus
_coremidi.MIDISourceCreate.argtypes = [MIDIClientRef, CFStringRef, POINTER(MIDIEndpointRef)]

_coremidi.MIDIDestinationCreate.restype = OSStatus
_coremidi.MIDIDestinationCreate.argtypes = [MIDIClientRef, CFStringRef, MIDIReadProc, c_void_p, POINTER(MIDIEndpointRef)]


def midi_source_create(client: MIDIClientRef, name: str) -> MIDIEndpointRef:
    endpoint = MIDIEndpointRef()
    cfname = cfstring_create(name)
    status = _coremidi.MIDISourceCreate(client, cfname, byref(endpoint))
    cfrelease(cfname)
    if status != 0:
        raise OSError(f"MIDISourceCreate failed with status {status}")
    return endpoint


def midi_destination_create(client: MIDIClientRef, name: str,
                            read_proc: MIDIReadProc) -> MIDIEndpointRef:
    endpoint = MIDIEndpointRef()
    cfname = cfstring_create(name)
    status = _coremidi.MIDIDestinationCreate(client, cfname, read_proc, None, byref(endpoint))
    cfrelease(cfname)
    if status != 0:
        raise OSError(f"MIDIDestinationCreate failed with status {status}")
    return endpoint


# --- Send / Receive ---

_coremidi.MIDISend.restype = OSStatus
_coremidi.MIDISend.argtypes = [MIDIPortRef, MIDIEndpointRef, POINTER(MIDIPacketList)]

_coremidi.MIDIReceived.restype = OSStatus
_coremidi.MIDIReceived.argtypes = [MIDIEndpointRef, POINTER(MIDIPacketList)]


def midi_send(port: MIDIPortRef, dest: MIDIEndpointRef,
              pktlist: MIDIPacketList) -> None:
    status = _coremidi.MIDISend(port, dest, byref(pktlist))
    if status != 0:
        raise OSError(f"MIDISend failed with status {status}")


def midi_received(source: MIDIEndpointRef, pktlist: MIDIPacketList) -> None:
    status = _coremidi.MIDIReceived(source, byref(pktlist))
    if status != 0:
        raise OSError(f"MIDIReceived failed with status {status}")


# --- Port connection ---

_coremidi.MIDIPortConnectSource.restype = OSStatus
_coremidi.MIDIPortConnectSource.argtypes = [MIDIPortRef, MIDIEndpointRef, c_void_p]

_coremidi.MIDIPortDisconnectSource.restype = OSStatus
_coremidi.MIDIPortDisconnectSource.argtypes = [MIDIPortRef, MIDIEndpointRef]


def midi_port_connect_source(port: MIDIPortRef, source: MIDIEndpointRef) -> None:
    status = _coremidi.MIDIPortConnectSource(port, source, None)
    if status != 0:
        raise OSError(f"MIDIPortConnectSource failed with status {status}")


def midi_port_disconnect_source(port: MIDIPortRef, source: MIDIEndpointRef) -> None:
    status = _coremidi.MIDIPortDisconnectSource(port, source)
    if status != 0:
        raise OSError(f"MIDIPortDisconnectSource failed with status {status}")


# --- Device / Source / Destination enumeration ---

_coremidi.MIDIGetNumberOfDevices.restype = ItemCount
_coremidi.MIDIGetNumberOfDevices.argtypes = []

_coremidi.MIDIGetDevice.restype = MIDIDeviceRef
_coremidi.MIDIGetDevice.argtypes = [ItemCount]

_coremidi.MIDIGetNumberOfSources.restype = ItemCount
_coremidi.MIDIGetNumberOfSources.argtypes = []

_coremidi.MIDIGetSource.restype = MIDIEndpointRef
_coremidi.MIDIGetSource.argtypes = [ItemCount]

_coremidi.MIDIGetNumberOfDestinations.restype = ItemCount
_coremidi.MIDIGetNumberOfDestinations.argtypes = []

_coremidi.MIDIGetDestination.restype = MIDIEndpointRef
_coremidi.MIDIGetDestination.argtypes = [ItemCount]

_coremidi.MIDIDeviceGetNumberOfEntities.restype = ItemCount
_coremidi.MIDIDeviceGetNumberOfEntities.argtypes = [MIDIDeviceRef]

_coremidi.MIDIDeviceGetEntity.restype = MIDIEntityRef
_coremidi.MIDIDeviceGetEntity.argtypes = [MIDIDeviceRef, ItemCount]

_coremidi.MIDIEntityGetNumberOfSources.restype = ItemCount
_coremidi.MIDIEntityGetNumberOfSources.argtypes = [MIDIEntityRef]

_coremidi.MIDIEntityGetSource.restype = MIDIEndpointRef
_coremidi.MIDIEntityGetSource.argtypes = [MIDIEntityRef, ItemCount]

_coremidi.MIDIEntityGetNumberOfDestinations.restype = ItemCount
_coremidi.MIDIEntityGetNumberOfDestinations.argtypes = [MIDIEntityRef]

_coremidi.MIDIEntityGetDestination.restype = MIDIEndpointRef
_coremidi.MIDIEntityGetDestination.argtypes = [MIDIEntityRef, ItemCount]


def get_number_of_devices() -> int:
    return _coremidi.MIDIGetNumberOfDevices()

def get_device(index: int) -> MIDIDeviceRef:
    return _coremidi.MIDIGetDevice(index)

def get_number_of_sources() -> int:
    return _coremidi.MIDIGetNumberOfSources()

def get_source(index: int) -> MIDIEndpointRef:
    return _coremidi.MIDIGetSource(index)

def get_number_of_destinations() -> int:
    return _coremidi.MIDIGetNumberOfDestinations()

def get_destination(index: int) -> MIDIEndpointRef:
    return _coremidi.MIDIGetDestination(index)


# --- Object properties ---

_coremidi.MIDIObjectGetStringProperty.restype = OSStatus
_coremidi.MIDIObjectGetStringProperty.argtypes = [MIDIObjectRef, CFStringRef, POINTER(CFStringRef)]


def get_endpoint_name(endpoint: MIDIEndpointRef) -> str:
    cfstr = CFStringRef()
    # kMIDIPropertyName is "name" as a CFStringRef
    prop_name = cfstring_create("name")
    status = _coremidi.MIDIObjectGetStringProperty(endpoint, prop_name, byref(cfstr))
    cfrelease(prop_name)
    if status != 0:
        return f"<unknown endpoint {endpoint}>"
    name = cfstring_to_str(cfstr)
    cfrelease(cfstr)
    return name


def get_device_name(device: MIDIDeviceRef) -> str:
    return get_endpoint_name(device)


# --- Packet construction ---

_coremidi.MIDIPacketListInit.restype = POINTER(MIDIPacket)
_coremidi.MIDIPacketListInit.argtypes = [POINTER(MIDIPacketList)]

_coremidi.MIDIPacketListAdd.restype = POINTER(MIDIPacket)
_coremidi.MIDIPacketListAdd.argtypes = [
    POINTER(MIDIPacketList), c_uint32, POINTER(MIDIPacket),
    MIDITimeStamp, c_uint32, POINTER(c_uint8),
]


def iter_packets(pktlist: MIDIPacketList) -> list[tuple[int, bytes]]:
    """Extract (timestamp, data) from all packets in a MIDIPacketList.

    MIDIPacketList is variable-length: packets are laid out contiguously
    with each packet's size = 10 + length, padded to 4-byte alignment.
    """
    results = []
    # Address of the first packet in the list
    offset = ctypes.addressof(pktlist.packet[0])
    for _ in range(pktlist.numPackets):
        ts = MIDITimeStamp.from_address(offset).value
        length = c_uint16.from_address(offset + 8).value
        data_ptr = (c_uint8 * length).from_address(offset + 10)
        results.append((ts, bytes(data_ptr)))
        # Advance: header (8 ts + 2 length) + data, padded to 4 bytes
        offset += (10 + length + 3) & ~3
    return results


def packet_list_init(pktlist: MIDIPacketList) -> POINTER(MIDIPacket):
    return _coremidi.MIDIPacketListInit(byref(pktlist))


def packet_list_add(pktlist: MIDIPacketList, pkt: POINTER(MIDIPacket),
                    timestamp: int, data: bytes) -> POINTER(MIDIPacket):
    list_size = ctypes.sizeof(pktlist)
    data_array = (c_uint8 * len(data))(*data)
    return _coremidi.MIDIPacketListAdd(
        byref(pktlist), list_size, pkt,
        MIDITimeStamp(timestamp), len(data), data_array,
    )


# --- Timing ---

# mach_absolute_time
_mach = ctypes.cdll.LoadLibrary('/usr/lib/libSystem.B.dylib')
_mach.mach_absolute_time.restype = c_uint64
_mach.mach_absolute_time.argtypes = []


class MachTimebaseInfo(Structure):
    _fields_ = [
        ('numer', c_uint32),
        ('denom', c_uint32),
    ]


_mach.mach_timebase_info.restype = c_int32
_mach.mach_timebase_info.argtypes = [POINTER(MachTimebaseInfo)]

_timebase_info: MachTimebaseInfo | None = None


def _get_timebase_info() -> MachTimebaseInfo:
    global _timebase_info
    if _timebase_info is None:
        _timebase_info = MachTimebaseInfo()
        _mach.mach_timebase_info(byref(_timebase_info))
    return _timebase_info


def mach_absolute_time() -> int:
    return _mach.mach_absolute_time()


def nanos_to_host_time(nanos: int) -> int:
    info = _get_timebase_info()
    return (nanos * info.denom) // info.numer


def host_time_to_nanos(host_time: int) -> int:
    info = _get_timebase_info()
    return (host_time * info.numer) // info.denom
