from .neuron_object import NeuronObject


class Mechanism(NeuronObject):
    def __init__(self, *args, **kwds):
        NeuronObject.__init__(self)


class DistributedMechanism(Mechanism):
    def __init__(self, *args, **kwds):
        Mechanism.__init__(self)


class PointProcess(Mechanism):
    def __init__(self, *args, **kwds):
        Mechanism.__init__(self)


class ArtificialCell(Mechanism):
    def __init__(self, *args, **kwds):
        Mechanism.__init__(self)
