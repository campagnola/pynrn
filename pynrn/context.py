# -*- coding: utf-8 -*-
import weakref
import os, sys, gc
from neuron import h
from .base_object import BaseObject


class Context(BaseObject):
    """ A NEURON simulation context. 

    Contexts encapsulate all sections, artificial cells, etc. that should be
    simulated together and provide methods for configuring and executing 
    simulations.

    Contexts are used to ensure complete separation between multiple
    simulation executions in a single running process. A typical context usage
    looks like:
    
    1. Create a Context instance.
    2. Build the objects in the neuron simulation
    3. Run the simulation one or more times
    4. Call Context.finish() before (optionally) repeating to step 1
    
    Only one context may be active at a time, and it is necessary to call 
    `finish()` on the currently active context before creating a new one, which
    will ensure that all NEURON objects have been removed and will not 
    interfere with the next simulation. An exception is made for Vectors to 
    ensure that their recorded data may be accessed at any time after the 
    simulation has run.

    If no Context exists at the time a NEURON object is created, then a default
    Context will be created and will become the active Context. This can be 
    accessed by calling `Context.active()`.
    
    
    Examples
    --------
    
    Creating a single-use context that will be automatically cleaned::
    
        from pynrn import Context, Section
        
        with Context() as sim:
            sec = Section()
            . . .
            sim.run(dt=0.01, tstop=10)
            
    Using the default context for simple simulations:
    
        from pynrn import Section, active_context
        
        sec = pynrn.Section()
        . . .
        sim = pynrn.active_context()
        sim.run(dt=0.01, tstop=10, celsius=37)
        
    """
    _active = None

    @classmethod
    def active_context(cls):
        """Return the currently active simulation context.
        """
        return cls._active
    
    def __init__(self, keep_vectors=True):
        if Context._active is not None:
            raise RuntimeError("There is already an active simulation context."
                               " Call Context.active.finish() before starting"
                               " another.")
        self._check_args(keep_vectors=bool)
        self._keep_vectors = keep_vectors
        self._objects = weakref.WeakSet()
        self._dt = 0.025
        self._celsius = 25.0
        self._tstop = 10.
        self._t = 0.0
        self._finitialized = False
        self._destroyed = False
        Context._active = self
        self._check_clean()
        
    def _add(self, obj):
        self._objects.add(obj)

    def _remove(self, obj):
        self._objects.remove(obj)
        
    @property
    def active(self):
        """Boolean indicating whether this is the currently active context.
        """
        return Context._active is self

    def _check_active(self):
        """Raise an exception if this context is not active.
        """
        if not self.active:
            raise RuntimeError("This context is no longer active; it cannot be"
                               " modified.")
        
    @property
    def dt(self):
        """ The timestep (in msec) for simulation output data.
        
        This is also the integration timestep used by NEURON when operating in
        fixed-timestep mode.
        """
        return self._dt
    
    @dt.setter
    def dt(self, dt):
        self._check_active()
        self._check_args(dt=float)
        dt = float(dt)
        self._check_bounds(dt="> 0")
        self._dt = dt

    @property
    def t(self):
        """ The current time (in msec) of the simulation.
        """
        return self._t

    @t.setter
    def t(self, t):
        self._check_active()
        self._check_args(t=float)
        t = float(t)
        self._t = t

    @property
    def celsius(self):
        """Temperature of the simulation (in deg. C)
        """
        return self._celsius
        
    @celsius.setter
    def celsius(self, celsius):
        self._check_active()
        self._check_args(celsius=float)
        celsius = float(celsius)
        self._celsius = celsius
        
    def init(self, dt=None, celsius=None, tstop=None, t=None, finit=True):
        """Initialize the simulation.
        
        Parameters
        ----------
        dt : float
            Optionally sets the simulation time step (in msec)
        celsius : float
            Optionally sets the simulation temperature (in degrees C)
        tstop : float
            Optionally sets the simulation stop time (in msec)
        t : float
            Optionally sets the simulation start time (in msec)
        finit : bool
            If True, this method calls NEURON's `finitialize()` routine.
            
            
        See also
        --------
        
        http://www.neuron.yale.edu/neuron/static/new_doc/simctrl/programmatic.html#finitialize
        """
        self._check_active()
        self._check_args(finit=bool)
        if finit and t is not None:
            raise TypeError("Cannot set t when finit==True.")
        
        if dt is not None:
            self.dt = dt
        if celsius is not None:
            self.celsius = celsius
        if tstop is not None:
            self.tstop = tstop
        if t is not None:
            self.t = t
        
        h.dt = self.dt
        h.celsius = self.celsius
        h.t = self.t
        
        if finit:
            h.finitialize()
            self._finitialized = True
            self.t = h.t
        
    def advance(self):
        """Run the NEURON simulator for one timestep.
        
        See also
        --------
        
        http://www.neuron.yale.edu/neuron/static/new_doc/simctrl/programmatic.html#fadvance
        """
        self._check_active()
        # make sure NEURON agrees with our variables
        self.init(finit=False)
        
        try:
            h.fadvance()
        finally:
            # update the clock
            self.t = h.t
        
    def run(self, **kwds):
        """Run the NEURON stimulator until the time reaches or passes tstop.
        
        All keyword parameters are passed to `init()`. By default, `init()` is 
        called with `finit=True` only if this has not been done previously. 
        """
        self._check_active()
        kwds.setdefault('finit', not self._finitialized)
        self.init(**kwds)
        
        tstop = self.tstop
        try:
            while h.t < tstop:
                h.fadvance()
        finally:
            self.t = h.t
    
    def finish(self):
        """Destroy all NEURON objects associated with this context.
        
        Calling this method ensures that the NEURON kernel is cleared and ready
        to begin a new simulation. If this method is not called before creating
        a new context, then an exception will be raised.
        
        This method is automatically called when exiting the context from a 
        `with` block.
        """
        self._destroy()
        if self.active:
            Context._active = None
        #sys.exc_clear()
        
    @property
    def finished(self):
        """Boolean indicating whether `finish()` has been called on this 
        Context. 
        """
        return self._destroyed
        
    def _destroy(self):
        # Todo: proper teardown of all objects in the correct order
        # SEE: http://www.neuron.yale.edu/phpBB/viewtopic.php?f=2&t=3213
        from .vector import Vector
        for o in list(self._objects):
            if self._keep_vectors and isinstance(o, Vector):
                continue
            o._destroy()
            
        # Workaround for reference leak:
        #   https://www.neuron.yale.edu/phpBB/viewtopic.php?f=2&t=3221
        #   https://www.neuron.yale.edu/phpBB/viewtopic.php?f=2&t=3296
        h.Vector().size()
            
        self._destroyed = True
    
    def verify(self):
        """Introspect the NEURON kernel to verify that the set of objects in
        this context exactly match those being simulated.
        
        If there is a mismatch, an exception is raised.
        """
        from . import (Section, Segment, DistributedMechanism, PointProcess, 
                       ArtificialCell, NetCon)

        # collect and sort all objects managed by this context
        allobjs = {Section: [], Segment: [], DistributedMechanism: [],
                   PointProcess: [], ArtificialCell: [], NetCon: []}
        deadobjs = dict([(k, []) for k in allobjs])
        for obj in self._objects:
            for k in allobjs:
                if isinstance(obj, k):
                    if obj.destroyed:
                        deadobjs[k].append(obj)
                    else:
                        allobjs[k].append(obj)
        
        # Note: need to be extra careful about leaking references from here!
        # NO exceptions allowed until NEURON references are removed!
        try:
            sec = None
            checked = set()
            extras = list()
            for sec in h.allsec():
                wrapper = Section._get(sec, create=False)
                if wrapper is None or wrapper not in self._objects:
                    raise RuntimeError("Section does not belong to this "
                                       "context: %s" % sec.name())
                checked.add(wrapper)
        finally:
            del sec
        
        # Context sections present that NEURON doesn't know about
        mysec = set([x for x in self._objects if isinstance(x, Section)])
        if mysec != checked:
            raise RuntimeError("Context has sections that are not known to "
                               "NEURON: %s" % (mysec - checked))
        
        # TODO: check for artificial cells, point processes, vectors, etc.
        
    def _check_clean(self):
        """Check that all objects have been cleared from NEURON kernel.
        """
        # Release objects held by an internal buffer
        # See https://www.neuron.yale.edu/phpBB/viewtopic.php?f=2&t=3221
        neuron.h.Vector().size()    
        
        # Make sure nothing is hanging around in reference cycles 
        gc.collect()
        
        remaining = []
        
        # No sections left
        n = len(list(h.allsec()))
        if n > 0:
            remaining.append((n, 'Section'))
            
        # NetCon (and other object types?)
        for objtyp in ['NetCon']:
            n = len(h.List('NetCon'))
            if n > 0:
                remaining.append((n, 'NetCon'))
        
        # No point processes or artificial cells left
        for name, typ in Mechanism.all_mechanism_types().items():
            if typ['artificial_cell'] or typ['point_process']:
                n = len(h.List(name))
                if n > 0:
                    remaining.append((n, name))
            
        if len(remaining) > 0:
            msg = ("Cannot create new context--old objects have not been "
                "cleared: %s" % ', '.join(['%d %s' % rem for rem in remaining]))
            raise RuntimeError(msg)

        
    def __enter__(self):
        self._check_active()
        return self
        
    def __exit__(self, *args):
        # An error occurred AND an environment variable was given allowing pynrn
        # to leave the context unfinished if an error occurred (to allow the
        # context to be inspected by a debugger).
        if args[0] is not None and os.getenv('PYNRN_DEBUG', '0') is not '0':
            return
        
        # Otherwise, clean up when exiting the context. 
        self.finish()


from .mechanism import Mechanism
