# -*- coding: utf-8 -*-
import numpy as np
from neuron import h
from .neuron_object import NeuronObject
from .reference import FloatVar

class Vector(NeuronObject):
    def __init__(self, *args):
        if isinstance(args[0], FloatVar):
            NeuronObject.__init__(self, h.Vector())
            self.record(*args)
        else:
            NeuronObject.__init__(self, h.Vector(*args))

    def __len__(self):
        return len(self.nrnobj)
        
    def record(self, ref, *args):
        self.check_destroyed()
        self._check_args(ref=(FloatVar))
        self.nrnobj.record(ref.get_ref(), *args)

    def play(self, *args):
        self.check_destroyed()
        args2 = []
        for arg in args:
            if isinstance(arg, Vector):
                args2.append(arg.nrnobj)
            elif isinstance(arg, FloatVar):
                args2.append(arg.get_ref())
            else:
                args2.append(arg)
        self.nrnobj.play(*args2)

    def play_remove(self):
        self.check_destroyed()
        self.nrnobj.play_remove()

    def asarray(self):
        # Note: we dont use numpy array interface because it fails silently
        # if there is a problem with the underlying Vector (for example, it
        # has already been deleted)
        if self.nrnobj is None:
            raise TypeError("Cannot convert vector to array because it has "
                             "already been deleted.")
        return np.array(self.nrnobj)
    
    def __array__(self):
        return self.asarray()
