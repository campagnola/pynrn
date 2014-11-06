from neuron import h
from .neuron_object import NeuronObject


class Mechanism(NeuronObject):
    """Base class for NEURON mechanisms including distributed mechanisms, 
    point processes, and artificial cells.
    
    Mechanisms should not be instantiated directly; use Section.insert()
    instead.
    """
    _mech_types = None
    
    def __init__(self, mech_type, segment, netcon_target, has_netevent, 
                 internal_type):
        NeuronObject.__init__(self)
        segment.insert(mech_type)
        self._netcon_target = netcon_target
        self._has_netevent = has_netevent
        self._internal_type = internal_type

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
    
    def create(self, type, section):
        mech_info = self.all_mechanism_types().get(type, None)
        
        if mech_info is None:
            raise KeyError("Unknown mechanism type '%s'. For a complete list, "
                           "see Mechanism.all_mechanism_types()." % type)
        
        pp = mech_info.pop('point_process')
        ac = mech_info.pop('artificial_cell')
        if pp:
            if ac:
                return ArtificialCell(type, section, **mech_info)
            else:
                return PointProcess(type, section, **mech_info)
        else:
            return DistributedMechanism(type, section, **mech_info)


class DistributedMechanism(Mechanism):
    def __init__(self, *args, **kwds):
        Mechanism.__init__(self)


class PointProcess(Mechanism):
    def __init__(self, *args, **kwds):
        Mechanism.__init__(self)


class ArtificialCell(Mechanism):
    def __init__(self, *args, **kwds):
        Mechanism.__init__(self)
