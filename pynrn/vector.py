# -*- coding: utf-8 -*-
import numpy as np
from neuron import h
from .neuron_object import NeuronObject
from .reference import FloatVar

class Vector(NeuronObject):
    def __init__(self, record=None):
        NeuronObject.__init__(self)
        self.__nrnobj = h.Vector()
        if record is not None:
            self.record(record)
            
    def record(self, ref):
        self.check_destroyed()
        self._check_args(ref=FloatVar)
        self.__nrnobj.record(ref._get_ref())
            
    def _destroy(self):
        NeuronObject._destroy(self)
        
    def asarray(self):
        # Note: we dont use numpy array interface because it fails silently
        # if there is a problem with the underlying Vector (for example, it
        # has already been deleted)
        if self.__nrnobj is None:
            raise TypeError("Cannot convert vector to array because it has "
                             "already been deleted.")
        return np.array(self.__nrnobj)
