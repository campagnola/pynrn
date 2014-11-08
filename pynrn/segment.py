import weakref
from .neuron_object import NeuronObject
from .reference import FloatVar
from .mechanism import DistributedMechanism

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
    def name(self):
        return self._section().name + "(%0.2f)" % self.x
        
    @property
    def x(self):
        """ The location of this segment (0 <= x <= 1) along the length of its 
        host section.
        """
        self.check_destroyed()
        return self.__nrnobj.x

    @property
    def v(self):
        """The membrane voltage of this segment in mV.
        """
        self.check_destroyed()
        return FloatVar(self, 'v', self.__nrnobj.v)

    @v.setter
    def v(self, v):
        self.check_destroyed()
        self.__nrnobj.v = v

    def area(self):
        """Return the area of the membrane for this segment.
        """
        self.check_destroyed()
        return self.__nrnobj.area()

    @property
    def diam(self):
        """Diameter of this segment in um.
        """
        self.check_destroyed()
        return FloatVar(self, 'diam', self.__nrnobj.diam)

    @diam.setter
    def diam(self, d):
        self.check_destroyed()
        self.__nrnobj.diam = d

    @property
    def ri(self):
        """Specific resistivity of the membrane for this segment in Ohm/cm^2.
        """
        self.check_destroyed()
        return FloatVar(self, 'ri', self.__nrnobj.ri)

    @ri.setter
    def ri(self, ri):
        self.check_destroyed()
        self.__nrnobj.ri = ri

    @property
    def cm(self):
        """Specific capacitance of this segment in uF/cm^2.
        """
        self.check_destroyed()
        return FloatVar(self, 'cm', self.__nrnobj.cm)

    @cm.setter
    def cm(self, cm):
        self.check_destroyed()
        self.__nrnobj.cm = cm

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
                mech = DistributedMechanism.create(_nrnobj=mech, segment=self)
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
