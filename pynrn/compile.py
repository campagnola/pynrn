import os
from neuron import h
from . import mechanism


def compile_and_load_mechanisms(path):
    """Compile .mod files located in *path* and load the compiled library.
    
    If a library file exists and is newer than the newest .mod file, it will not be recompiled.
    """
    mech_files = [f for f in os.listdir(path) if f.endswith('.mod')]
    newest = max([os.path.getmtime(os.path.join(path, f)) for f in mech_files])
    mechlib_path = os.path.join(path, 'x86_64/.libs/libnrnmech.so')
    if not os.path.exists(mechlib_path) or os.path.getmtime(mechlib_path) < newest:
        os.system(f'cd {path}; nrnivmodl')
    load_mechanisms(path)


_loaded_mechanisms = {}
def load_mechanisms(path):
    """Load the compiled mechanisms from the given path.

    If the mechanism library has already been loaded and the .so file has not been modified since,
    then it will not be reloaded.
    """
    global _loaded_mechanisms
    mechlib = os.path.join(path, 'x86_64/.libs/libnrnmech.so')
    mtime = os.path.getmtime(mechlib)
    if mechlib in _loaded_mechanisms and _loaded_mechanisms[mechlib] == mtime:
        return
    if os.path.isfile(mechlib):
        h.nrn_load_dll(mechlib)    
    mechanism.Mechanism.reload_mechanism_types()
    _loaded_mechanisms[mechlib] = mtime
