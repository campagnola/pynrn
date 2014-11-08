import weakref
from neuron import h
from .neuron_object import NeuronObject
from .reference import FloatVar
import collections


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
        self._name = self.__nrnobj.name()
        self._mech_desc = self.all_mechanism_types()[self._name]

        # Populate all dynamic attributes from the mechanism.
        # We are ignoring 'globals' because these to not appear to be 
        # accessible in python.
        suffix = '_' + self._name
        for group in ['parameters', 'assigned', 'state']:
            for vname,vsize in self._mech_desc[group].items():
                if vname.endswith(suffix):
                    vname = vname[:-len(suffix)]
                self._variables.append(vname)
                # Add name to __dict__ so that dir() lists available attributes.
                self.__dict__[vname] = None

    @property
    def name(self):
        return self._name

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
        elif attr in self.__dict__.get('_variables', []):
            self.check_destroyed()
            setattr(self.__nrnobj, attr, val)
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
    
    #@classmethod
    #def create(cls, type, *args, **kwds):
        #mech_info = cls.all_mechanism_types().get(type, None)
        #if mech_info is None:
            #raise KeyError("Unknown mechanism type '%s'. For a complete list, "
                           #"see Mechanism.all_mechanism_types()." % type)
        #mech_info = mech_info.copy()
        
        #pp = mech_info.pop('point_process')
        #ac = mech_info.pop('artificial_cell')
        #for k in mech_info:
            #if k in kwds:
                #raise TypeError("Invalid keyword argument %s" % k)
        #kwds.update(mech_info)
        #kwds['mech_type'] = type
        
        #if pp:
            #if ac:
                #return ArtificialCell(*args, **kwds)
            #else:
                #return PointProcess(*args, **kwds)
        #else:
            #return DistributedMechanism(*args, **kwds)

# Cache this data now because the results from MechanismStandard change
# after some interactions with NEURON. See:
# http://www.neuron.yale.edu/phpBB/viewtopic.php?f=8&t=3219
Mechanism.all_mechanism_types()


#class DistributedMechanism(Mechanism):
    #def __init__(self, section, **kwds):
        #Mechanism.__init__(self, **kwds)
        #self._section = weakref.ref(section)
        #section._insert(self)
    
    #@property
    #def section(self):
        #return self._section()

    #def remove(self):
        #"""Remove this mechanism from its host section.
        
        #After removal, the mechanism may not be re-used.
        #"""
        #raise NotImplementedError()


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
        self._segment = weakref.ref(kwds.pop('segment'))
        Mechanism.__init__(self, **kwds)


class PointProcess(Mechanism):
    def __init__(self, x, section):
        if not isinstance(x, float):
            raise TypeError("x argument must be float (got %s)." % type(x))
        if not isinstance(section, Section):
            raise TypeError("section argument must be Section instance (got %s)."
                            % type(section))
        self._section = weakref.ref(section)
        self._x = x
        try:
            pproc = getattr(h, self.__class__.__name__)(pos, section)
            Mechanism.__init__(self, _nrnobj=pproc)
        finally:
            if 'pproc' in locals():
                del pproc


class ArtificialCell(Mechanism):
    def __init__(self):
        try:
            cell = getattr(h, self.__class__.__name__)()
            Mechanism.__init__(self, _nrnobj=cell)
        finally:
            if 'cell' in locals():
                del cell
