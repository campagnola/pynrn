import weakref
from .neuron_object import NeuronObject
from .reference import FloatVar
from .mechanism import SegmentMechanism

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
        self._section = weakref.ref(kwds['section'])
        self._mechs = {}
        self._update_mechs()
        
    @property
    def x(self):
        self.check_destroyed()
        return self.__nrnobj.x

    @property
    def v(self):
        self.check_destroyed()
        return FloatVar(self, 'v', self.__nrnobj.v)

    @v.setter
    def v(self, v):
        self.check_destroyed()
        self.__nrnobj.v = v

    @property
    def mechanisms(self):
        """A dictionary of all distributed mechanisms in this Segment.
        """
        self.check_destroyed()
        return self._mechs.copy()

    def _get_ref(self, attr):
        """Return a reference to a variable on the underlying NEURON object
        """
        # Note: variable references do not increase the refcount of their 
        # host Section.
        self.check_destroyed()
        objname = '_' + self.__class__.__name__ + '__nrnobj'
        nrnobj = getattr(self, objname)
        return getattr(nrnobj, '_ref_' + attr)

    def _destroy(self):
        if self.destroyed:
            return
        self.__nrnobj = None
        for mech in self._mechs.values():
            mech._destroy()
        self._mechs = {}
        NeuronObject._destroy(self)

    def _update_mechs(self):
        """Update the list of distributed mechanisms in this segment.
        """
        self.check_destroyed()
        try:
            # Add newly-added mechanisms
            allnames = []
            for mech in self.__nrnobj:
                name = mech.name()
                allnames.append(name)
                if name in self._mechs:
                    continue
                mech = SegmentMechanism(_nrnobj=mech, segment=self)
                self._mechs[name] = mech
                setattr(self, name, mech)
            
            # Remove mechanisms that no longer exist
            for name in self._mechs:
                if name not in allnames:
                    self._mechs[name]._destroy()
                    del self._mechs[name]
                    delattr(self, name)
            
        finally:
            # make sure NEURON objects can't be trapped in exception frame
            del mech
