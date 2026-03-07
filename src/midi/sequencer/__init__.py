"""Platform-agnostic sequencer interface.

Auto-selects the appropriate backend (ALSA on Linux, CoreMIDI on macOS).
"""
import sys

if sys.platform.startswith('linux'):
    try:
        from ..sequencer_alsa.sequencer import *
    except ImportError:
        pass
elif sys.platform == 'darwin':
    try:
        from ..sequencer_osx.sequencer import *
    except ImportError:
        pass
