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
    
    def __init__(self):
        if Context._active is not None:
            raise RuntimeError("There is already an active simulation context."
                               " Call finish() on that context before starting"
                               " another.")
        self._objects = []
        self._dt = 0.025
        self._celsius = 25.0
        self._tstop = 10.
        self._initialized = False
        Context._active = self
        
    def _add(self, obj):
        self._objects.append(obj)
        
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
        h.fadvance()
        
    def run(self, **kwds):
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
        for o in self._objects:
            o._destroy()
    