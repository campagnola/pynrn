import weakref
from .neuron_object import NeuronObject
from .reference import FloatVar
from .mechanism import DistributedMechanism, PointProcess


# Todo: decide whether to disambiguate 'Segment'.
#   - A segment is a sub-compartment of a section
#   - A segment is also a reference to a location along a section.
#   Should this class be renamed to SectionLocation or similar?

class Segment(NeuronObject):
    """Segments are pointers to a specific location on a Section.
    """
    def __init__(self, **kwds):
        if '_nrnobj' not in kwds:
            raise TypeError("Segment instances should only be accessed from Sections.")
        self._mechs = {}
        self._section = weakref.ref(kwds['section'])
        NeuronObject.__init__(self, kwds['_nrnobj'])
        self._update_mechs()

    @property
    def name(self):
        """The name of the segment, defined as "section_name(location)".
        """
        return self._section().name + "(%0.2f)" % self.x
    
    @property
    def section(self):
        """The section instance to which this Segment belongs.
        """
        return self._section()
    
    @property
    def x(self):
        """ The location of this segment (0 <= x <= 1) along the length of its 
        host section.
        """
        self.check_destroyed()
        return self.nrnobj.x

    @property
    def v(self):
        """The membrane voltage of this segment in mV.
        """
        self.check_destroyed()
        return FloatVar(self, 'v', self.nrnobj.v)

    @v.setter
    def v(self, v):
        self.check_destroyed()
        self._check_args(v=float)
        v = float(v)
        self.nrnobj.v = v

    @property
    def area(self):
        """Return the surface area of the membrane for this segment.
        """
        self.check_destroyed()
        return self.nrnobj.area()

    @property
    def diam(self):
        """Diameter of this segment in um.
        """
        self.check_destroyed()
        return FloatVar(self, 'diam', self.nrnobj.diam)

    @diam.setter
    def diam(self, diam):
        self.check_destroyed()
        self._check_args(diam=float)
        diam = float(diam)
        self._check_bounds(diam='> 0')
        self.nrnobj.diam = diam

    @property
    def ri(self):
        """Axial resistance from the center of the segment to either end.
        
        Computed as::
        
            .01 * sec.Ra * (sec.L / (2*sec.nseg)) / (pi * (seg.diam / 2)**2)
            
        See also
        --------
        
        http://www.neuron.yale.edu/neuron/static/new_doc/modelspec/programmatic/topology/geometry.html#stylized-specification-of-geometry
        """
        self.check_destroyed()
        return self.nrnobj.ri()

    @property
    def cm(self):
        """Specific capacitance of this segment in uF/cm^2.
        """
        self.check_destroyed()
        return FloatVar(self, 'cm', self.nrnobj.cm)

    @cm.setter
    def cm(self, cm):
        self.check_destroyed()
        self._check_args(cm=float)
        cm = float(cm)
        self.nrnobj.cm = cm

    @property
    def mechanisms(self):
        """A dictionary of all distributed mechanisms in this Segment.
        """
        self.check_destroyed()
        return self._mechs.copy()

    @property
    def point_processes(self):
        """A list of all point processes attached to this Segment.
        """
        all_pp = []
        try:
            for pp in self.nrnobj.point_processes():
                all_pp.append(PointProcess._get(pp))
        finally:
            if 'pp' in locals():
                del pp
                # flush locals cache to remove hiden refs
                # https://bugs.python.org/issue6116
                locals()
        return all_pp

    def get_ref(self, attr):
        """Return a reference to a variable on the underlying NEURON object
        """
        # Note: variable references do not increase the refcount of their 
        # host Section.
        self.check_destroyed()
        return getattr(self.nrnobj, '_ref_' + attr)

    def _destroy(self):
        if self.destroyed:
            return
        for mech in self._mechs.values():
            if not mech.destroyed:  # may have already been destroyed by context
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
            for mech in self.nrnobj:
                name = mech.name()
                allnames.append(name)
                if name in self._mechs:
                    continue
                mech = DistributedMechanism.create(_nrnobj=mech, segment=self)
                self._mechs[name] = mech
                setattr(self, name, mech)
            
            # Remove mechanisms that no longer exist
            rem = []
            for name in self._mechs:
                if name not in allnames:
                    self._mechs[name]._destroy()
                    rem.append(name)
            for name in rem:
                del self._mechs[name]
                delattr(self, name)
            
        finally:
            # make sure NEURON objects can't be trapped in exception frame
            if 'mech' in locals():
                del mech
                # flush locals cache to remove hiden refs
                # https://bugs.python.org/issue6116
                locals()
