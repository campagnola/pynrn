# -*- coding: utf-8 -*-
import weakref, gc
from neuron import h
from .context import Context
from .base_object import BaseObject


class NeuronObject(BaseObject):
    """ Base for all NEURON objects.
    
    Provides:
    * private handle to underlying NEURON object
      (must stay private or else we cannot ensure _destroy will work)
    * methods for creating / destroying underlying object
    """
    def __init__(self, nrn_object):
        # Add this object to the currently active context
        ctx = Context.active_context()
        if ctx is None:
            ctx = Context()
        self.__context = ctx
        ctx._add(self)
        self.__destroyed = False
        self.__nrnobj = nrn_object

    @property
    def nrnobj(self):
        return self.__nrnobj

    @property
    def context(self):
        """The Context to which this object belongs.
        """
        return self.__context
    
    @property
    def destroyed(self):
        """Bool indicating whether the underlying NEURON object has been 
        destroyed.
        """
        return self.__destroyed

    def check_destroyed(self):
        if self.__destroyed:
            raise RuntimeError("Underlying NEURON object has already been "
                               "destroyed.")
    
    def _destroy(self):
        """ Destroy the underlying NEURON object(s).
        
        The default implementation only removes this object from its parent
        context; subclasses must extend this method to remove references to
        NEURON objects.
        """
        self.__nrnobj = None
        # h.Vector().size()
        if self.__destroyed:
            print(f"Attempt to destroy NEURON object {self} twice")
            return
        self.__destroyed = True
        self.__context._remove(self)
            