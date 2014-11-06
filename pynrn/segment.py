from .neuron_object import NeuronObject
from .reference import FloatVar

# Todo: decide whether to disambiguate 'Segment'.
#   - A segment is a sub-compartment of a section
#   - A segment is also a reference to a location along a section.
#   Should this class be renamed to SectionLocation or similar?

class Segment(NeuronObject):
    """Segments are pointers to a specific location on a Section.
    """
    def __init__(self, **kwds):
        NeuronObject.__init__(self)
        if '_nrnobj' not in kwds:
            raise TypeError("Segment instances should only be accessed from Sections.")
        self.__nrnobj = kwds['_nrnobj']
        
    @property
    def x(self):
        return self.__nrnobj.x

    @property
    def v(self):
        return FloatVar(self, 'v', self.__nrnobj.v)

    @v.setter
    def v(self, v):
        self.__nrnobj.v = v

    def _get_ref(self, attr):
        """Return a reference to a variable on the underlying NEURON object
        """
        # Note: variable references do not increase the refcount of their 
        # host Section.
        objname = '_' + self.__class__.__name__ + '__nrnobj'
        nrnobj = getattr(self, objname)
        return getattr(nrnobj, '_ref_' + attr)

    def _destroy(self):
        self.__nrnobj = None
        NeuronObject._destroy(self)
