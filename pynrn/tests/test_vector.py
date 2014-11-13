# -*- coding: utf-8 -*-
import pynrn
import numpy as np


def test_vector():
    with pynrn.Context() as sim:
        sec = pynrn.Section()
        sec.insert('hh')
        
        
        v1 = pynrn.Vector(sec(0.5).v)
        v2 = pynrn.Vector()
        v2.record(sec(0.5).hh.gk)
        
        sim.init()
        vm = sec(0.5).v
        gk = sec(0.5).hh.gk
        sim.run(dt=0.01, tstop=1)
        
        v1 = v1.asarray()
        v2 = v2.asarray()
        
        assert v1[0] == vm
        assert v2[0] == gk
        assert v1.shape == v2.shape == (101,)
        
        