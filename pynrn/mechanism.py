# -*- coding: utf-8 -*-
import weakref
from neuron import h
from .neuron_object import NeuronObject
from .reference import FloatVar
import collections


# Note: this list is extended at the end of the module.
__all__ = ['Mechanism', 'DistributedMechanism', 'PointProcess', 
           'ArtificialCell']


class Mechanism(NeuronObject):
    """Base class for NEURON mechanisms including distributed mechanisms, 
    point processes, and artificial cells.
    
    Mechanisms should not be instantiated directly; use Section.insert()
    instead.
    """
    _mech_types = None
    
    def __init__(self, **kwds):
        # Disable __setattr__ until init has completed.
        NeuronObject.__init__(self)
        self._variables = []
        self.__nrnobj = kwds.pop('_nrnobj')
        self._mech_name = kwds.pop('mech_name')
        self._mech_desc = self.all_mechanism_types()[self._mech_name]

        # Populate all dynamic attributes from the mechanism.
        # We are ignoring 'globals' because these to not appear to be 
        # accessible in python.
        suffix = '_' + self._mech_name
        for group in ['parameters', 'assigned', 'state']:
            for vname,vsize in self._mech_desc[group].items():
                if vname.endswith(suffix):
                    vname = vname[:-len(suffix)]
                self._variables.append(vname)
                # Add name to __dict__ so that dir() lists available attributes.
                self.__dict__[vname] = None

    @property
    def mechanism_name(self):
        return self._mech_name

    def __getattribute__(self, attr):
        """If a mechanism variable is requested, then return a FloatVar reference
        to that value. Otherwise, just do a normal attribute lookup.
        """
        if attr.startswith('_'):
            return NeuronObject.__getattribute__(self, attr)
        
        if attr in self._variables:
            self.check_destroyed()
            return FloatVar(self, attr, getattr(self.__nrnobj, attr))
        else:
            return NeuronObject.__getattribute__(self, attr)
    
    def __setattr__(self, attr, val):
        """Set the value of a mechanism variable.
        
        Raise NameError if the name is not recognized. Names beginning with 
        an underscore will be assigned as normal python attributes.
        """
        if attr.startswith('_'):
            return NeuronObject.__setattr__(self, attr, val)
        
        if hasattr(self, attr):
            if attr in self.__dict__.get('_variables', []):
                self.check_destroyed()
                setattr(self.__nrnobj, attr, val)
            else:
                return NeuronObject.__setattr__(self, attr, val)
        else:
            raise NameError("Unknown attribute '%s' for mechanism '%s'." % 
                            (attr, self._name))

    def _get_ref(self, attr):
        self.check_destroyed()
        return getattr(self.__nrnobj, '_ref_' + attr)

    @property
    def variables(self):
        """A list of all variable names for this mechanism.
        """
        return self._variables[:]

    @property
    def is_netcon_target(self):
        """Boolean indicating whether this mechanism can receive NetCon events.
        """
        return self._mech_desc['netcon_target']
        
    @property
    def has_net_event(self):
        """Boolean indicating whether this mechanism can be a source for
        NetCon events.
        
        Notes
        -----
        
        All ArtificialCell mechanisms can be a source for NetCon
        events, regardless of the value of the has_net_event property. See
        the NEURON documentation on MechanismType for more information.
        """
        return self._mech_desc['has_netevent']
        
    @property
    def internal_type(self):
        return self._mech_desc['internal_type']
        
    @staticmethod
    def all_mechanism_types():
        """Return a dictionary of all available mechanism types.
        
        Each dictionary key is the name of a mechanism and each value is
        another dictionary containing information about the mechanism::
        
            mechanism_types = {
                'mech_name1': {
                    'point_process': bool,
                    'artificial_cell': bool,
                    'netcon_target': bool,
                    'has_netevent': bool,
                    'internal_type': int,
                    'globals': {name:size, ...},
                    'parameters': {name:size, ...},
                    'assigned': {name:size, ...},
                    'state': {name:size, ...},
                },
                'mech_name2': {...},
                'mech_name3': {...},
                ...
            }
        
        * point_process: False for distributed mechanisms, True for point 
          processes and artificial cells.
        * artificial_cell: True for artificial cells, False otherwise
        * netcon_target: True if the mechanism can receive NetCon events
        * has_netevent: True if the mechanism can emit NetCon events
        * internal_type: Integer specifying the NEURON internal type index of 
          the mechanism
        * globals: dict of the name and vector size of the mechanism's global
          variables
        * parameters: dict of the name and vector size of the mechanism's 
          parameter variables
        * assigned: dict of the name and vector size of the mechanism's 
          assigned variables
        * state: dict of the name and vector size of the mechanism's state
          variables
          
        For more information on global, parameter, assigned, and state 
        variables see:
        http://www.neuron.yale.edu/neuron/static/docs/help/neuron/nmodl/nmodl.html
        """
        if Mechanism._mech_types is None:
            Mechanism._mech_types = collections.OrderedDict()
            mname = h.ref('')
            # Iterate over two mechanism types (distributed, point/artificial)
            for i in [0, 1]:
                mt = h.MechanismType(i)
                nmech = int(mt.count())
                # Iterate over all mechanisms of this type
                for j in range(nmech):
                    mt.select(j)
                    mt.selected(mname)
                    
                    # General mechanism properties
                    name = mname[0]  # convert hoc string ptr to python str
                    
                    desc = {
                        'point_process': bool(i),
                        'netcon_target': bool(mt.is_netcon_target(j)),
                        'has_netevent': bool(mt.has_net_event(j)),
                        'artificial_cell': bool(mt.is_artificial(j)),
                        'internal_type': int(mt.internal_type()),
                    }
                    
                    # Collect information about 4 different types of variables
                    for k,ptype in [(-1, 'globals'), (1, 'parameters'), 
                                    (2, 'assigned'), (3, 'state')]:
                        desc[ptype] = {} # collections.OrderedDict()
                        ms = h.MechanismStandard(name, k)
                        for l in range(int(ms.count())):
                            psize = ms.name(mname, l)
                            pname = mname[0]  # parameter name
                            desc[ptype][pname] = int(psize)
                    
                    # Assemble everything in one place
                    Mechanism._mech_types[name] = desc
                
        return Mechanism._mech_types

    def _destroy(self):
        if self.destroyed:
            return
        self.__nrnobj = None
        NeuronObject._destroy(self)


# Cache this data now because the results from MechanismStandard change
# after some interactions with NEURON. See:
# http://www.neuron.yale.edu/phpBB/viewtopic.php?f=8&t=3219
Mechanism.all_mechanism_types()


class DistributedMechanism(Mechanism):
    """A distributed membrane mechanism used in a single segment.
    
    Range variables for the mechanism acting at this segment may be accessed
    as attributes. See the ``variable_names`` property for a complete list.
    
    This class should not be instantiated directly; instead use 
    ``segment.mechname``.
    """
    def __init__(self, **kwds):
        if '_nrnobj' not in kwds:
            raise TypeError("DistributedMechanism instances should only be "
                            "accessed from Segments.")
        kwds['mech_name'] = kwds['_nrnobj'].name()
        self._segment = weakref.ref(kwds.pop('segment'))
        Mechanism.__init__(self, **kwds)

    @classmethod
    def create(self, **kwds):
        cls = globals()['DistributedMechanism_' + kwds['_nrnobj'].name()]
        return cls(**kwds)
        
    @property
    def segment(self):
        return self._segment()
        
    @property
    def name(self):
        return self.segment.name + "." + self.mechanism_name
    

class PointProcess(Mechanism):
    """Point processes are mechanisms that act on a single Segment.
    
    Notes
    -----
    
    Several methods of the original PointProcess class are changed:
    * .loc() => .attach()  
    * .has_loc() => .attached
    * .get_segment() => .segment
    * .get_loc() => .segment.x
    """
    all_point_processes = weakref.WeakValueDictionary()
    
    def __init__(self, loc=None, sec=None, name=None):
        from .section import Section
        from .segment import Segment
        
        self._check_args(loc=(Segment, float, type(None)),
                         sec=(Section, type(None)),
                         name=(str, type(None)))
        self._section = None
        
        try:
            mech_name = self.__class__.__name__
            pproc = getattr(h, mech_name)()
            self.__nrnobj = pproc  # we'll keep a separate ref from Mechanism
            Mechanism.__init__(self, _nrnobj=pproc, mech_name=mech_name)
            if name is None:
                name = pproc.hname()
            self._name = name
            PointProcess.all_point_processes[pproc.hname()] = self
        finally:
            if 'pproc' in locals():
                del pproc
        
        if isinstance(loc, Segment):
            if sec is not None:
                raise TypeError("Argument sec must be None if loc is a Segment.")
            self.attach(loc)
        elif loc is not None:
            # For backward compatibility with NEURON
            loc = float(loc)
            if not isinstance(sec, Section):
                raise TypeError("Argument sec must be a Section instance when loc is float.")
            self.attach(sec(loc))
        elif sec is not None:
            raise TypeError("Argument sec is invalid if loc is None.")
    
    @classmethod
    def _get(cls, pproc):
        """Return the existing PointProcess instance for the specified NEURON 
        point process. 
        
        Raise an exception if no instance is found.
        """
        try:
            return PointProcess.all_point_processes[pproc.hname()]
        finally:
            del pproc

    @property
    def name(self):
        """The name given to this point process at initialization time.
        """
        return self._name

    @property
    def attached(self):
        """Boolean indicating whether this point process is currently attached
        to a section.
        """
        self.check_destroyed()
        attached = self.__nrnobj.has_loc() == 1.0
        if not attached:
            self._section = None
        return attached

    def attach(self, segment):
        """Attach this point process to a specific segment.
        
        This method may be called any number of times to re-attach the point
        process to other sections or to different segments on the same 
        section (each call automatically disconnects the point process from its
        previous attachment).
        
        Parameters
        ----------
        segment : Segment
            Specifies the exact segment (section + location) to attach to.
            
        Notes
        -----
        
        When the point process is attached, it moves to the _center_ of the 
        segment containing the requested location. If the number of segments
        in the section changes, then the point process will again move to the
        nearest segment center. It is therefore recommended to set the location
        of the point process only _after_ setting the number of segments in the
        section.
        
        This method replaces the original PointProcess.loc().
        """
        self.check_destroyed()
        from .segment import Segment
        self._check_args(segment=Segment)
        
        self._section = weakref.ref(segment.section)
        
        # warning: don't use pproc.loc(float) because this uses CAS to 
        # set section
        self.__nrnobj.loc(segment._Segment__nrnobj)
    
    @property
    def section(self):
        """The section that this point process is attached to, or None if it
        is not attached.
        """
        if not self.attached:
            return None
        # warning: do not use pproc.get_segment() because this apparently
        # creates a reference leak in NEURON. 
        # https://www.neuron.yale.edu/phpBB/viewtopic.php?f=2&t=3221
        return self._section()

    @property
    def segment(self):
        """The Segment that this point process is attached to, or None if it
        is not attached.
        """
        if not self.attached:
            return None
        # warning: do not use pproc.get_segment() because this apparently
        # creates a reference leak in NEURON
        # https://www.neuron.yale.edu/phpBB/viewtopic.php?f=2&t=3221
        return self.section(self.__nrnobj.get_loc())

    #@property
    #def location(self):
        #"""The location of the point process (0 to 1) along the length of its 
        #host section, or None if the point process is not attached to a 
        #section.
        
        #Setting this property causes the point process to move to a new 
        #location within the section it is currently attached to.
        #"""
        #if not self.attached:
            #return None
        #return self.__nrnobj.get_loc()

    #@location.setter
    #def location(self, loc):
        #self.check_destroyed()
        #try:
            #loc = float(loc)
        #except Exception:
            #raise TypeError("location must be float (got %s)." % type(loc))
        #self.attach(self.section(loc))

    def _destroy(self):
        if self.destroyed:
            return
        self.__nrnobj = None
        Mechanism._destroy(self)


class ArtificialCell(Mechanism):
    """Artificial cells are mechanisms that generate net events; they do not 
    interact directly with any cell membranes.
    """
    def __init__(self, name=None):
        try:
            mech_name = self.__class__.__name__
            cell = getattr(h, mech_name)()
            Mechanism.__init__(self, _nrnobj=cell, mech_name=mech_name)
            if name is None:
                name = cell.hname()
            self._name = name
        finally:
            if 'cell' in locals():
                del cell

    @property
    def name(self):
        """The name given to this artificial cell at initialization time.
        """
        return self._name
        

# make new subclasses for all mechanism types
all_mechs = Mechanism.all_mechanism_types()
for name,mech in all_mechs.items():
    if not mech['point_process']:
        m_class = type('DistributedMechanism_' + name, (DistributedMechanism,), {})
    else:
        if mech['artificial_cell']:
            m_class = type(name, (ArtificialCell,), {})
        else:
            m_class = type(name, (PointProcess,), {})
        __all__.append(m_class.__name__)
    globals()[m_class.__name__] = m_class
