"""
Modern, pythonic API for NEURON.

The goal of pynrn is to provide a clean API for NEURON that avoids many of
the idiosyncracies and common pitfalls encountered when working with NEURON.
This API attempts to preserve most of the vocabulary and workflow of legacy 
NEURON, but does not attempt to provide complete compatibility. 

Features:

* Proper python classes for all NEURON object types
* Introspection of NEURON kernel 
* Explicit and automatic creation / deletion of underlying NEURON objects
* Fully documented, unit-tested API
* No HocObjects
* Pure python (but depends on standard neuron package)

Todo:
* Multiple simulation contexts

"""
__version__ = "1.0"

from .context import Context
from .section import Section
from .segment import Segment
from .mechanism import *
from .vector import Vector
from .netcon import NetCon
