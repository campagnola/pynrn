import weakref
import collections
import keyword
from neuron import h
from .neuron_object import NeuronObject
from .reference import FloatVar

# Note: this list is extended at the end of the module.
__all__ = ['Mechanism', 'DistributedMechanism', 'PointProcess', 
           'ArtificialCell']


class Mechanism(NeuronObject):
    """Base class for NEURON mechanisms including distributed mechanisms, 
    point processes, and artificial cells.
    """
    _mech_types = None
    
    def __init__(self, nrn_object, mech_name, **kwds):
        # Disable __setattr__ until init has completed.        
        NeuronObject.__init__(self, nrn_object)
        self._variables = []
        self._mech_name = mech_name
        self._mech_desc = self.all_mechanism_types()[self._mech_name]

        # Populate all dynamic attributes from the mechanism.
        # We are ignoring 'globals' because these to not appear to be 
        # accessible in python.
        suffix = '_' + self._mech_name
        for group in ['parameters', 'assigned', 'state']:
            for vname,vsize in self._mech_desc[group].items():
                if vname.endswith(suffix):
                    vname = vname[:-len(suffix)]
                if vname == 'del':
                    # this translation applies to IClamp; hopefully others as well..
                    vname = 'delay'
                if keyword.iskeyword(vname):
                    vname += "_"
                self._variables.append(vname)
                # Add name to __dict__ so that dir() lists available attributes.
                self.__dict__[vname] = None

    def _set_attrs(self, **kwds):
        for kwd, val in kwds.items():
            try:
                setattr(self, kwd, val)
            except AttributeError:
                self._destroy()  # make sure we disconnect!
                raise TypeError('Invalid keyword argument "%s".' % kwd)    

    @property
    def mechanism_name(self):
        return self._mech_name

    def __getattribute__(self, attr):
        """If a mechanism variable is requested, then return a FloatVar reference
        to that value. Otherwise, just do a normal attribute lookup.
        """
        try:
            if attr.startswith('_'):
                return NeuronObject.__getattribute__(self, attr)
            nrnobj = NeuronObject.__getattribute__(self, 'nrnobj')
            if attr in self._variables:
                self._check_attrs_usable()
                return FloatVar(self, attr, getattr(self.nrnobj, attr.rstrip('_')))
            elif hasattr(nrnobj, attr):
                # mainly to allow forwarding to mechanism methods
                decorator = NeuronObject.__getattribute__(self, '_func_args_to_neuron')
                decorated = decorator(getattr(nrnobj, attr))
                return decorated
            else:
                return NeuronObject.__getattribute__(self, attr)
        except AttributeError:
            raise
        except Exception as exc:
            # Don't let python swallow exceptions here!
            raise BaseException(*exc.args)
    
    def __setattr__(self, attr, val):
        """Set the value of a mechanism variable.
        
        Raise AttributeError if the name is not recognized. Names beginning with 
        an underscore will be assigned as normal python attributes.
        """
        if attr.startswith('_'):
            return NeuronObject.__setattr__(self, attr, val)
        
        if hasattr(self, attr):
            if attr in self.__dict__.get('_variables', []):
                self._check_attrs_usable()
                setattr(self.nrnobj, attr.rstrip('_'), val)
            else:
                return NeuronObject.__setattr__(self, attr, val)
        else:
            raise AttributeError("Unknown attribute '%s' for mechanism '%s'." % 
                                 (attr, self._name))

    def get_ref(self, attr):
        self.check_destroyed()
        return getattr(self.nrnobj, '_ref_' + attr.rstrip('_'))

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
            Mechanism.reload_mechanism_types()                
        return Mechanism._mech_types

    @staticmethod
    def reload_mechanism_types():
        """Load metadata about all available mechanism types from NEURON, then create
        subclasses for each mechanism type.
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
                if name in Mechanism._mech_types:
                    continue

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
        Mechanism.create_mechanism_classes()

    @staticmethod
    def create_mechanism_classes():
        # make new subclasses for all mechanism types
        all_mechs = Mechanism.all_mechanism_types()
        for name,mech in all_mechs.items():
            if not mech['point_process']:
                name = 'DistributedMechanism_' + name
                superclass = DistributedMechanism
            else:
                if mech['artificial_cell']:
                    superclass = ArtificialCell
                else:
                    superclass = PointProcess

            if name in globals():
                continue

            m_class = type(name, (superclass,), {})
            __all__.append(m_class.__name__)
            globals()[m_class.__name__] = m_class

    def _destroy(self):
        NeuronObject._destroy(self)
        
        # workaround for reference leak
        # https://www.neuron.yale.edu/phpBB/viewtopic.php?f=2&t=3221
        # Note: this replaces one leaked reference with another (more benign) one.
        h.Vector().size()

    def _check_attrs_usable(self):
        self.check_destroyed()



class DistributedMechanism(Mechanism):
    """A distributed membrane mechanism used in a single segment.
    
    Range variables for the mechanism acting at this segment may be accessed
    as attributes. See the ``variable_names`` property for a complete list.
    
    This class should not be instantiated directly; instead use 
    ``segment.mechname``.
    """
    def __init__(self, _nrnobj, segment):
        self._segment = weakref.ref(segment)
        Mechanism.__init__(self, nrn_object=_nrnobj, mech_name=_nrnobj.name())

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

    Parameters
    ----------
    segment : Segment
        The segment to which this point process should be attached.
    name : str
        An optional name for this point process.
    
    All extra keyword arguments are used to set properties of the point 
    process.
        
    Notes
    -----
    
    Several methods of the original PointProcess class are changed:
    * .loc() => .attach()  
    * .has_loc() => .attached
    * .get_segment() => .segment
    * .get_loc() => .segment.x
    """
    all_point_processes = weakref.WeakValueDictionary()
    
    def __init__(self, segment=None, name=None, **kwds):
        from .segment import Segment
        
        self._check_args(segment=(Segment, type(None)),
                         name=(str, type(None)))
        self._section = None
        
        mech_name = self.__class__.__name__
        pproc = getattr(h, mech_name)()
        try:
            Mechanism.__init__(self, nrn_object=pproc, mech_name=mech_name, **kwds)
            if name is None:
                name = pproc.hname()
            self._name = name
            PointProcess.all_point_processes[pproc.hname()] = self
        finally:
            del pproc
        
        if segment is not None:
            self.attach(segment)

        self._set_attrs(**kwds)

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
        attached = self.nrnobj.has_loc() == 1.0
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
        self.nrnobj.loc(segment.nrnobj)
    
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
        return self.section(self.nrnobj.get_loc())

    def _destroy(self):
        if self.destroyed:
            return
        n = len(h.List(self.__class__.__name__))
        Mechanism._destroy(self)
        assert len(h.List(self.__class__.__name__)) == n-1

    def _check_attrs_usable(self):
        Mechanism._check_attrs_usable(self)
        if not self.attached:
            raise RuntimeError("Cannot set point process attributes until it is"
                               " attached.")


class ArtificialCell(Mechanism):
    """Artificial cells are mechanisms that generate net events; they do not 
    interact directly with any cell membranes.
    """
    def __init__(self, name=None, **kwds):
        mech_name = self.__class__.__name__
        cell = getattr(h, mech_name)()
        try:
            Mechanism.__init__(self, nrn_object=cell, mech_name=mech_name, **kwds)
            if name is None:
                name = cell.hname()
            self._name = name
        finally:
            del cell

        self._set_attrs(**kwds)

    @property
    def name(self):
        """The name given to this artificial cell at initialization time.
        """
        return self._name



# Cache this data now because the results from MechanismStandard change
# after some interactions with NEURON. See:
# http://www.neuron.yale.edu/phpBB/viewtopic.php?f=8&t=3219
Mechanism.reload_mechanism_types()


# Compile and load mechanisms built in to pynrn, but not included in NEURON.
import os
import pynrn.compile
mech_path = os.path.join(os.path.dirname(__file__), 'mechanisms')

if 'VecStim' not in globals():
    pynrn.compile.compile_and_load_mechanisms(mech_path)
