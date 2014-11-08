import weakref
from .context import Context

class NeuronObject(object):
    """ Base for all NEURON objects.
    
    Provides:
    * private handle to underlying NEURON object
      (must stay private or else we cannot ensure _destroy will work)
    * methods for creating / destroying underlying object
    """
    def __init__(self):
        # Add this object to the currently active context
        ctx = Context.active()
        if ctx is None:
            ctx = Context()
        self.__context = ctx
        ctx._add(self)
        self.__destroyed = False

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
        if self.destroyed:
            raise RuntimeError("Underlying NEURON object has already been "
                               "destroyed.")
        
    def _destroy(self):
        """ Destroy the underlying NEURON object(s).
        
        The default implementation only removes this object from its parent
        context; subclasses must extend this method to remove references to
        NEURON objects.
        """
        if self.__destroyed:
            return
        self.__context._remove(self)
        self.__destroyed = True

