import weakref
import inspect
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
    
    def _check_args(self, **kwds):
        """Basic input type-checking.
        
        Keyword arguments are the names of variables to check in the 
        caller's scope. Argument values give a type or tuple of types allowed.
        If float or int types are given, the value is checked by attempting
        to coerce it to float/int.
        
        Example::
        
            self._check_args(
                section=Section,  # argument must be Section instance
                pproc=(PointProcess, type(None)),  # must be PointProcess or None
                x=float))  # succeeds if float(x) is possible
            
        """
        caller_locals = inspect.currentframe().f_back.f_locals
        updates = {}
        for kwd, types in kwds.items():
            if not isinstance(types, tuple):
                types = (types,)
                
            val = caller_locals[kwd]
            
            # If the arg is not already one of the required types, then see if
            # it can be converted.
            if not isinstance(val, types):
                for ctype in (float, int):
                    if ctype in types:
                        try:
                            val = ctype(val)
                            break
                        except Exception:
                            pass
            
            # If no conversions were possible, then raise TypeError
            if not isinstance(val, types):
                names = tuple([typ.__name__ for typ in types])
                if len(names) > 2:
                    names = ', '.join(names[:-1]) + ', or ' + names[-1]
                else:
                    names = ' or '.join(names)
                raise TypeError("Argument %s must be %s (got %s)." % 
                                (kwd, names, type(caller_locals[kwd]).__name__))

    def _check_bounds(self, **kwds):
        """Input boundary checking.
        
        Keyword arguments are the names of variables to check in the 
        caller's scope. Argument values give a tuple of strings that will be 
        evaluated with the checked variable to determine its validity.
        
        Example::
        
            self._check_bounds(
                x=(">= 0", "<= 1"),
                y=("> 0"))
        """
        caller_locals = inspect.currentframe().f_back.f_locals
        for kwd, bounds in kwds.items():
            if not isinstance(bounds, tuple):
                bounds = (bounds,)
            for check in bounds:
                if not eval(kwd + check, {}, caller_locals):
                    bounds = [b.strip() for b in bounds]
                    if len(bounds) < 3:
                        cond = ' and '.join(bounds)
                    else:
                        cond = ', '.join(bounds[:-1]) + ', and ' + bounds[-1]
                    raise ValueError("Argument %s must be %s (got %s)." % 
                                     (kwd, cond, caller_locals[kwd]))

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
        if self.__destroyed:
            return
        self.__context._remove(self)
        self.__destroyed = True

