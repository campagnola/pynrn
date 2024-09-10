# -*- coding: utf-8 -*-
import weakref
from neuron import h

from .neuron_object import NeuronObject
from .reference import FloatVar


class NetCon(NeuronObject):
    """
    Network Connection object that defines a synaptic connection between a source and target. 
    
    When the source variable passes threshold in the positive direction at time t-delay, the target will receive an event at time t along with weight information.
    
    Parameters
    ----------
    source : FloatRef | event source
        Source variable used to determine when network events are generated.
        When the source crosses *threshold* in the positive direction, an event
        is delivered to *target*. Usually *source* is a reference to a segment
        membrane potential.
    target : PointProcess, ArtificialCell, or None
        The recipient of network events. Must have target.has_netevent == True.
        If None, the NetCon is inactive but can still be used to record 
        threshold crossings (see NetCon.record).
    threshold : float
        Source variable threshold to generate a network event.
    delay : float >= 0
        Time (in msec) to wait between threshold crossing and event delivery.
    weight : float
        Arbitrary value carried with network event. The target may use this 
        value when processing the event.
    
    
    Examples
    --------
    
        sec1 = Section()
        sec2 = Section()
        syn = AlphaSynapse(0.5, sec2)
        nc = NetCon(sec1(0.5).v, syn, threshold=-20, delay=5, weight=1)
    
    
    See Also
    --------
    
    NEURON documentation:
    http://www.neuron.yale.edu/neuron/static/new_doc/modelspec/programmatic/network/netcon.html
    """
    def __init__(self, source, target, threshold=10, delay=1, weight=0):
        from .mechanism import PointProcess, ArtificialCell

        self._check_args(source=(FloatVar, NeuronObject),
                         target=(PointProcess, ArtificialCell, type(None)),
                         threshold=float,
                         delay=float,
                         weight=float)
        self._check_bounds(delay=">= 0")
        threshold = float(threshold)
        delay = float(delay)
        weight = float(weight)
        if isinstance(target, PointProcess) and not target.attached:
            raise TypeError("PointProcess target must be attached to a Section "
                            "before connecting NetCon.")
        
        self._source_obj = source

        if isinstance(source, FloatVar):
            # source section must be CAS
            source.source.section._push()
            if target is None:
                self._target = None
                nrnobj = h.NetCon(source.get_ref(), h.ref(None), threshold, delay, weight)
            else:
                self._target = weakref.ref(target)
                nrnobj = h.NetCon(source.get_ref(), target.nrnobj, threshold, delay, weight)
            NeuronObject.__init__(self, nrnobj)
            h.pop_section()
        else:
            nrnobj = h.NetCon(source.nrnobj, target.nrnobj, threshold, delay, weight)
            NeuronObject.__init__(self, nrnobj)

        
        self._weight = NetConWeight(self)

    @property
    def target(self):
        if self._target is None:
            return None
        return self._target()

    @target.setter
    def target(self, target):
        from .mechanism import PointProcess, ArtificialCell
        self._check_args(target=(PointProcess, ArtificialCell, type(None)))
        if isinstance(target, PointProcess) and not target.attached:
            raise TypeError("PointProcess target must be attached to a Section "
                            "before connecting NetCon.")
        if target is None:
            self._target = None
            self.nrnobj.setpost(h.ref(None))
        else:
            self._target = weakref.ref(target)
            self.nrnobj.setpost(target.nrnobj)
        
        if self._weight is not None:
            self._weight._update_count()
            self._weight = None

    @property
    def source(self):
        return self._source_obj

    @property
    def delay(self):
        return self.nrnobj.delay
    
    @delay.setter
    def delay(self, delay):
        self._check_args(delay=float)
        delay = float(delay)
        self.nrnobj.delay = delay

    @property
    def weight(self):
        return self._weight
    
    @weight.setter
    def weight(self, weight):
        self.weight[:] = weight

    @property
    def threshold(self):
        return self.nrnobj.threshold
    
    @threshold.setter
    def threshold(self, threshold):
        self._check_args(threshold=float)
        threshold = float(threshold)
        self.nrnobj.threshold = threshold

    @property
    def valid(self):
        return self.nrnobj.valid() == 1.0
    
    @property
    def active(self):
        return self.nrnobj.active() == 1.0
    
    @active.setter
    def active(self, act):
        self._check_args(act=bool)
        self.nrnobj.active(act)
        
    def event(self, tdeliver, flag=None):
        """Deliver an event at time *tdeliver*.
        """
        self._check_args(tdeliver=float)
        tdeliver = float(tdeliver)
        
        if flag is None:
            self.nrnobj.event(tdeliver)
        else:
            self.nrnobj.event(tdeliver, flag)
    
    def _destroy(self):
        n_nc = len(h.List('NetCon'))
        NeuronObject._destroy(self)
        assert len(h.List('NetCon')) < n_nc, f"Failed to destroy {self}"

    
class NetConWeight(object):
    def __init__(self, netcon):
        self._nc = weakref.ref(netcon)
        self._update_count()
    
    def __len__(self):
        return self._len
    
    def __getitem__(self, item):
        item = int(item)
        if item < -len(self) or item >= len(self):
            raise IndexError("Index %d out of bounds for weight vector of length %d." %
                             (item, len(self)))
        return self._nc().nrnobj.weight[item]
    
    def __getslice__(self, slice):
        inds = slice.indices(len(self))
        w = []
        for i in range(*inds):
            w.append(self[i])
        return w
    
    def __setitem__(self, item, val):
        item = int(item)
        val = float(val)
        if item < -len(self) or item >= len(self):
            raise IndexError("Index %d out of bounds for weight vector of length %d." %
                             (item, len(self)))
        self._nc().nrnobj.weight[item] = val
        
    def __setslice__(self, slice, vals):
        try:
            val = float(vals)
            scalar = True
        except Exception:
            scalar = False
        
        inds = range(*slice.indices(len(self)))
        if not scalar and len(inds) != len(vals):
            raise TypeError("Cannot set %d weight values with sequence of length %d." % 
                            len(inds), len(vals))
        for i,j in enumerate(inds):
            if scalar:
                self[j] = val
            else:
                self[j] = vals[i]
    
    def __iter__(self):
        for i in range(len(self)):
            yield self[i]
    
    def __repr__(self):
        return repr(list(self))

    def _update_count(self):
        self._len = int(self._nc().nrnobj.wcnt())
