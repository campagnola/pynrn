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
        ctx = Context.active()
        if ctx is None:
            ctx = Context()
        self._context = ctx
        ctx._add(self)
        # keep the reference to the NEURON object very private
        attr = '_' + self.__class__.__name__ + '__nrnobj'
        setattr(self, attr, None)
        
    def _create(self):
        """ Create the underlying NEURON object.
        
        This must be implemented in subclasses and must set the __nrnobj 
        attribute.
        """
        raise NotImplementedError
    
    def _destroy(self):
        """ Destroy the underlying NEURON object.
        """
        attr = '_' + self.__class__.__name__ + '__nrnobj'
        assert hasattr(self, attr)
        setattr(self, attr, None)
