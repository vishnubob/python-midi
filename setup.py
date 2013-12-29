#!/usr/bin/env python

from distutils.core import setup, Extension

__base__ = {
    'name':'midi', 
    'version':'v0.2.3',
    'description':'Python MIDI API',
    'author':'giles hall',
    'author_email':'ghall@csh.rit.edu',
    'package_dir':{'midi':'src'},
    'py_modules':['midi.containers', 'midi.__init__', 'midi.events', 'midi.util', 'midi.fileio', 'midi.constants'],
    'ext_modules':[],
    'ext_package':'',
    'scripts':['scripts/mididump.py', 'scripts/mididumphw.py', 'scripts/midiplay.py'],
}

def setup_alsa(ns):
    srclist = ["src/sequencer_alsa/sequencer_alsa.i"]
    extns = {
        'libraries':['asound'],
        #'extra_compile_args':['-DSWIGRUNTIME_DEBUG']
    }
    ext = Extension('_sequencer_alsa', srclist, **extns)
    ns['ext_modules'].append(ext)

    ns['package_dir']['midi.sequencer'] = 'src/sequencer_alsa'
    ns['py_modules'].append('midi.sequencer.__init__')
    ns['py_modules'].append('midi.sequencer.sequencer')
    ns['py_modules'].append('midi.sequencer.sequencer_alsa')
    ns['ext_package'] = 'midi.sequencer'

def configure_platform():
    from sys import platform
    ns = __base__.copy()
    # currently, only the ALSA sequencer is supported
    if platform.startswith('linux'):
        setup_alsa(ns)
        pass
    else:
        print "No sequencer available for '%s' platform." % platform
    return ns

if __name__ == "__main__":
    setup(**configure_platform())


