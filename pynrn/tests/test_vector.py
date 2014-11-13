# -*- coding: utf-8 -*-
import pynrn
import numpy as np


def test_vector():
    with pynrn.Context() as sim:
        sec = pynrn.Section()
        sec.insert('hh')
        
        vm = sec(0.5).v
        gk = sec(0.5).hh.gk
        
        v1 = pynrn.Vector(sec(0.5).v)
        v2 = pynrn.Vector()
        v2.record(sec(0.5).hh.gk)
        
        sim.run(dt=0.01, tstop=1)
        
        v1 = v1.array()
        v2 = v2.array()
        
        assert v1[0] == vm
        assert v2[0] == gk
        assert v1.shape == v2.shape == 100
        
        