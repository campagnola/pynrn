# -*- coding: utf-8 -*-
import pytest
import numpy as np
import pynrn
from pynrn.reference import FloatVar

def test_segment():
    with pynrn.Context():
        
        sec = pynrn.Section()
        seg = sec(0.5)
        assert seg.section is sec
        assert seg.x == 0.5
        assert sec.name in seg.name

        sec.insert('hh')
        assert 'hh' in seg.mechanisms
        
        # test range variables
        assert isinstance(seg.v, FloatVar)
        assert seg.v.source is seg
        assert seg.v.name == 'v'
        assert seg.v == seg.nrnobj.v
        assert isinstance(seg.hh, pynrn.DistributedMechanism)
        assert isinstance(seg.hh.gkbar, FloatVar)
        assert seg.hh.gkbar.source is seg.hh
        assert seg.hh.gkbar.name is 'gkbar'
        
        # test property assignments work as expected
        seg.v = 0
        assert seg.v == 0
        assert seg.nrnobj.v == 0
        
        seg.hh.gkbar = 2
        assert seg.hh.gkbar == 2
        
        seg.diam = 10
        assert seg.diam == 10
        assert seg.nrnobj.diam == 10
        assert np.allclose(seg.area, sec.L * np.pi * seg.diam)
        
        seg.diam = 100
        assert np.allclose(seg.area, sec.L * np.pi * seg.diam)        
        
        seg.cm = 100
        assert seg.cm == 100
        assert seg.nrnobj.cm == 100
        
        # test ri works
        cross_area = 3.14159 * (seg.diam / 2)**2
        half_length = sec.L / (2 * sec.nseg)
        ri = .01 * sec.Ra * half_length / cross_area
        assert np.allclose(seg.ri, ri)
        
        # check for invalid property assignments
        with pytest.raises(ValueError):
            seg.diam = 0
        with pytest.raises(ValueError):
            seg.diam = -10
        with pytest.raises(TypeError):
            seg.diam = 'x'
        with pytest.raises(TypeError):
            seg.v = 'x'
        with pytest.raises(TypeError):
            seg.cm = 'x'
        
        # check for read-only properties
        with pytest.raises(AttributeError):
            seg.section = 1
        with pytest.raises(AttributeError):
            seg.name = 1
        with pytest.raises(AttributeError):
            seg.x = 1
        with pytest.raises(AttributeError):
            seg.area = 1
        with pytest.raises(AttributeError):
            seg.ri = 1

        # Don't allow manual creation of segments
        with pytest.raises(TypeError):
            pynrn.Segment()
            
        