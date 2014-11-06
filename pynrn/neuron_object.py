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
        self._context = ctx
        ctx._add(self)
        
    def _destroy(self):
        """ Destroy the underlying NEURON object(s).
        
        The default implementation only removes this object from its parent
        context; subclasses must extend this method to remove references to
        NEURON objects.
        """
        self._context._remove(self)
