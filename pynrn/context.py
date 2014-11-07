import weakref
from neuron import h


class Context(object):
    """ A NEURON simulation context. 

    Contexts encapsulate all sections, artificial cells, etc. that should be
    simulated together and provide methods for configuring and executing 
    simulations.

    Contexts are used to ensure complete separation between multiple
    simulation executions in a single running process.
    """
    _active = None

    @classmethod
    def active(cls):
        """Return the currently active simulation context.
        """
        return cls._active
    
    def __init__(self, finish_on_error=True):
        if Context._active is not None:
            raise RuntimeError("There is already an active simulation context."
                               " Call finish() on that context before starting"
                               " another.")
        self._finish_on_error = finish_on_error
        self._objects = weakref.WeakSet()
        self._dt = 0.025
        self._celsius = 25.0
        self._tstop = 10.
        self._initialized = False
        Context._active = self
        self.verify()
        
    def _add(self, obj):
        self._objects.add(obj)

    def _remove(self, obj):
        self._objects.remove(obj)
        
    @property
    def dt(self):
        """ The timestep (in msec) for simulation output data.
        
        This is also the integration timestep used by NEURON when operating in
        fixed-timestep mode.
        """
        return self._dt
    
    @dt.setter
    def dt(self, dt):
        if self._initialized:
            raise RuntimeError("Cannot change timestep after initialization.")
        self._dt = dt

    @property
    def t(self):
        """ The current time (in msec) of the simulation.
        """
        return h.t

    @property
    def celsius(self):
        """Temperature of the simulation (in deg. C)
        """
        return self._celsius
        
    @celsius.setter
    def celsius(self, celsius):
        self._celsius = celsius
        
    def init(self, dt=None, celsius=None, tstop=None, finit=True):
        if dt is not None:
            self.dt = dt
        if celsius is not None:
            self.celsius = celsius
        if tstop is not None:
            self.tstop = tstop
        
        h.dt = self.dt
        h.celsius = self.celsius
        
        if finit:
            h.finitialize()
        self._initialized = True
        
    def advance(self):
        """Run the NEURON simulator for one timestep.
        """
        h.fadvance()
        
    def run(self, **kwds):
        """Run the NEURON stimulator until the time reaches or passes tstop.
        
        All keyword arguments are used to inintialize the context, if it has 
        not already been initialized. 
        
        If the context has already been initialized, no arguments will be 
        accepted.
        """
        if not self._initialized:
            self.init(**kwds)
        elif len(kwds) > 0:
            raise TypeError("Cannot accept arguments to run() because this "
                            "context has already been initialized.")
        
        tstop = self.tstop
        while h.t < tstop:
            h.fadvance()
    
    def finish(self):
        self._destroy()
        Context._active = None
        
    def _destroy(self):
        # SEE: http://www.neuron.yale.edu/phpBB/viewtopic.php?f=2&t=3213
        for o in list(self._objects):
            o._destroy()
    
    def verify(self):
        """Introspect the NEURON kernel to verify that the set of objects in
        this context exactly match those being simulated.
        
        If there is a mismatch, an exception is raised.
        """
        from .section import Section
        
        # Note: need to be extra careful about leaking references from here!
        # NO exceptions allowed until NEURON references are removed!
        try:
            sec = None
            checked = set()
            extras = list()
            for sec in h.allsec():
                wrapper = Section._get(sec, create=False)
                if wrapper is None:
                    extras.append(sec.name())
                else:
                    checked.add(wrapper)
        finally:
            del sec
        
        # NEURON secions present that the context doesn't know about
        if len(extras) > 0:
            raise Exception("Section(s) do not belong to this context: %s" %
                        str(extras))
        
        # Context sections present that NEURON doesn't know about
        mysec = set([x for x in self._objects if isinstance(x, Section)])
        if len(mysec - checked) > 0:
            raise Exception("Context has sections that are not known to "
                            "NEURON: %s" % mysec)
        
        # TODO: check for artificial cells, point processes, vectors, etc.
        
        
    def __enter__(self):
        return self
        
    def __exit__(self, *args):
        self.finish()
