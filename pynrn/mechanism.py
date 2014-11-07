import weakref
from neuron import h
from .neuron_object import NeuronObject
from .reference import FloatVar

class Mechanism(NeuronObject):
    """Base class for NEURON mechanisms including distributed mechanisms, 
    point processes, and artificial cells.
    
    Mechanisms should not be instantiated directly; use Section.insert()
    instead.
    """
    _mech_types = None
    
    def __init__(self, mech_type, netcon_target, has_netevent, internal_type):
        NeuronObject.__init__(self)
        self._netcon_target = netcon_target
        self._has_netevent = has_netevent
        self._internal_type = internal_type
        self._mech_type = mech_type

    @property
    def type(self):
        return self._mech_type

    @property
    def is_netcon_target(self):
        """Boolean indicating whether this mechanism can receive NetCon events.
        """
        return self._netcon_target
        
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
        return self._has_netevent
        
    @property
    def internal_type(self):
        return self._internal_type
        
    @staticmethod
    def all_mechanism_types():
        """Return a dictionary of all available mechanism types.
        
        Each dictionary key is the name of a mechanism and each value is
        another dictionary containing information about the mechanism:
        
        * point_process: False for distributed mechanisms, True for point 
          processes and artificial cells.
        * artificial_cell: True for artificial cells, False otherwise
        * netcon_target: True if the mechanism can receive NetCon events
        * has_netevent: True if the mechanism can emit NetCon events
        * internal_type: Integer specifying the NEURON internal type index of 
          the mechanism
        """
        if Mechanism._mech_types is None:
            Mechanism._mech_types = {}
            mname = h.ref('')
            for i in [0, 1]:
                mt = h.MechanismType(i)
                nmech = int(mt.count())
                for j in range(nmech):
                    mt.select(j)
                    mt.selected(mname)
                    is_nct = bool(mt.is_netcon_target(j))
                    has_ne = bool(mt.has_net_event(j))
                    is_art = bool(mt.is_artificial(j))
                    int_typ = int(mt.internal_type())
                    Mechanism._mech_types[mname[0]] = {
                        'point_process': bool(i),
                        'netcon_target': is_nct,
                        'has_netevent': has_ne, 
                        'artificial_cell': is_art,
                        'internal_type': int_typ}
                
        return Mechanism._mech_types

    @classmethod
    def create(cls, type, *args, **kwds):
        mech_info = cls.all_mechanism_types().get(type, None)
        if mech_info is None:
            raise KeyError("Unknown mechanism type '%s'. For a complete list, "
                           "see Mechanism.all_mechanism_types()." % type)
        mech_info = mech_info.copy()
        
        pp = mech_info.pop('point_process')
        ac = mech_info.pop('artificial_cell')
        for k in mech_info:
            if k in kwds:
                raise TypeError("Invalid keyword argument %s" % k)
        kwds.update(mech_info)
        kwds['mech_type'] = type
        
        if pp:
            if ac:
                return ArtificialCell(*args, **kwds)
            else:
                return PointProcess(*args, **kwds)
        else:
            return DistributedMechanism(*args, **kwds)


class DistributedMechanism(Mechanism):
    def __init__(self, section, **kwds):
        Mechanism.__init__(self, **kwds)
        self._section = weakref.ref(section)
        section._insert(self)
    
    @property
    def section(self):
        return self._section()

    def remove(self):
        """Remove this mechanism from its host section.
        
        After removal, the mechanism may not be re-used.
        """
        raise NotImplementedError()


class SegmentMechanism(NeuronObject):
    """Provides access to a distributed mechanism within a single segment.
    
    Range variables for the mechanism acting at this segment may be accessed
    as attributes. See the ``variable_names`` property for a complete list.
    
    This class should not be instantiated directly; instead use 
    ``segment.mechname``.
    """
    def __init__(self, **kwds):
        # Disable __setattr__ until init has completed.
        self.__dict__['_setattr_disabled'] = True
        self.__dict__['_varnames'] = []
        
        NeuronObject.__init__(self)
        if '_nrnobj' not in kwds:
            raise TypeError("SegmentMechanism instances should only be "
                            "accessed from Segments.")
        
        self._segment = kwds['segment']
        self.__nrnobj = kwds['_nrnobj']
        self._name = self.__nrnobj.name()
        
        # Activate __setattr__ only after initial attributes have been created.
        self._setattr_disabled = False
        
        suffix = '_' + self._name
        for name in dir(self.__nrnobj):
            if not name.endswith(suffix):
                continue
            name = name[:-len(suffix)]
            self._varnames.append(name)
            # Add name to __dict__ so that dir() lists available attributes.
            self.__dict__[name] = None
    
    @property
    def variable_names(self):
        """A list of the names of variables for this mechanism.
        """
        return self._varnames[:]
    
    def __getattribute__(self, attr):
        """If a mechanism variable is requested, then return a FloatVar reference
        to that value. Otherwise, just do a normal attribute lookup.
        """
        ignore_attrs = ['_setattr_disabled', '_varnames', '__dict__']
        if attr not in ignore_attrs and attr in self._varnames:
            self.check_destroyed()
            val = getattr(self.__nrnobj, attr)
            return FloatVar(self, attr, val)
        else:
            return NeuronObject.__getattribute__(self, attr)
    
    def __setattr__(self, attr, val):
        """Set the value of a mechanism variable.
        
        Raise NameError if the name is not recognized. 
        """
        if attr in self._varnames:
            self.check_destroyed()
            setattr(self.__nrnobj, attr, val)
        else:
            # allow setting atrtibutes that already exist, also
            # allow setting any attributes during init.
            if self._setattr_disabled or hasattr(self, attr):
                return NeuronObject.__setattr__(self, attr, val)
            
            raise NameError("Unknown attribute '%s' for mechanism '%s'." % 
                            (attr, self._name))

    def _get_ref(self, attr):
        self.check_destroyed()
        return getattr(self.__nrnobj, '_ref_' + attr)
    
    @property
    def name(self):
        return self._name


class PointProcess(Mechanism):
    def __init__(self, segment, **kwds):
        Mechanism.__init__(self, **kwds)
        self._segment = weakref.ref(segment)

    @property
    def segment(self):
        return self._segment()


class ArtificialCell(Mechanism):
    def __init__(self, **kwds):
        Mechanism.__init__(self, **kwds)
