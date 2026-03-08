CLI Tools
=========

The package installs several command-line scripts for working with MIDI
files and devices.

mididump
--------

Print the contents of a MIDI file as readable Python representations::

    $ mididump mary.mid

midiplay
--------

Play a MIDI file to a hardware device::

    $ midiplay <client> <port> <midi_file>

mididumphw
----------

List MIDI hardware and software devices attached to the system::

    $ mididumphw

midirecord
----------

Record MIDI input from a device to a file::

    $ midirecord <source_endpoint_ref> <output.mid> [duration_seconds]

midilisten
----------

Listen to a MIDI device and print events in real time::

    $ midilisten <client> <port>
