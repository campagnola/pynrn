import pytest
import pynrn
import numpy as np


def test_distributed():
    with pynrn.Context():
        sec = pynrn.Section()
        sec.nseg = 10
        sec.insert('hh')
        midseg = sec(0.5)
        
        # Test setting mechanism range variables
        for i,seg in enumerate(sec):
            seg.hh.gkbar = i
            assert seg.hh.gkbar == i
            # check that nearby segments get the same value
            assert sec(seg.x+0.01).hh.gkbar == i
    
        # test inserting new mechanisms updates existing segments
        sec.insert('pas')
        assert 'pas' in sec.mechanisms
        assert 'pas' in dir(midseg)
        assert 'pas' in midseg.mechanisms
        
        # Setting segment count results in new segments that are properly 
        # decorated
        sec.nseg = 20
        assert 'pas' in sec(0.9).mechanisms
        assert 'hh' in sec(0.9).mechanisms


def test_pointprocess():
    # Test creation / deletion
    # (this has caused reference leaks in the past)
    with pynrn.Context():
        sec = pynrn.Section()
        ic = pynrn.IClamp(name="some name")
        ic.attach(sec(0.1))
        ic.segment
    
    with pynrn.Context():
        sec = pynrn.Section()
        sec.nseg = 2
        ic = pynrn.IClamp(name="some name")
        assert len(sec.point_processes) == 0
        
        assert ic.name == "some name"
        assert not ic.attached
        
        ic.attach(sec(0.1))
        assert ic.attached
        assert ic.segment is sec(0.25)
        assert ic.segment.section is sec
        
        assert sec.point_processes == [ic]
        assert sec(0.25).point_processes == [ic]
        assert sec(0.1).point_processes == [ic]
        assert sec(0.75).point_processes == []
        
        sec2 = pynrn.Section()
        ic2 = pynrn.IClamp(sec2(0.2))
        
        assert ic2.attached
        assert ic2.segment is sec2(0.5)

        ic2.attach(sec(0.75))
        ic.attach(sec(0.25))
        
        assert sec2.point_processes == []
        assert set(sec.point_processes) == set([ic, ic2])
        assert sec(0.75).point_processes == [ic2]
        assert sec(0.25).point_processes == [ic]

        ic2.attach(sec(0.2))
        assert set(sec.point_processes) == set([ic, ic2])
        assert sec(0.75).point_processes == []
        assert set(sec(0.25).point_processes) == set([ic, ic2])
        
        sec2.nseg = 23
        sec.nseg = 32
    
    