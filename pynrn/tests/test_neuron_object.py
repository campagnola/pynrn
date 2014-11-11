import pytest
from pynrn.neuron_object import NeuronObject
import pynrn

def test_arg_checks():
    with pynrn.Context():
        o = NeuronObject()
        x = 1
        y = 0.2
        z = "asd"
        w = None
        o._check_args(x=int, y=float, z=str, o=NeuronObject, w=(int, type(None)))
        o._check_args(x=(type(None), NeuronObject, float), y=float)
        o._check_args(x=(type(None), NeuronObject, float), y=int)
        
        with pytest.raises(TypeError):
            o._check_args(x=str)
        with pytest.raises(TypeError):
            o._check_args(y=type(None))
        with pytest.raises(TypeError):
            o._check_args(x=float, y=int, z=(NeuronObject, int))

        o._check_bounds(x='> 0', y=('< 100', '>= 0'))
        
        with pytest.raises(ValueError):
            o._check_bounds(x='< 1')
        with pytest.raises(ValueError):
            o._check_bounds(y=('< 100', '> 1'))
        