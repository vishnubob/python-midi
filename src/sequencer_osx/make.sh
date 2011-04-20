swig -python sequencer_osx.i 
gcc -shared -framework CoreFoundation -framework CoreMIDI -I/usr/local/include/python2.6 -L/usr/local/lib -lpython sequencer_osx_wrap.c  -o _sequencer_osx.so
