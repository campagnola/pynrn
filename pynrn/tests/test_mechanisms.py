# -*- coding: utf-8 -*-
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
    # Test workaround for reference leak
    # https://www.neuron.yale.edu/phpBB/viewtopic.php?f=2&t=3221
    with pynrn.Context():
        sec = pynrn.Section()
        ic = pynrn.IClamp(name="some name")
        ic.attach(sec(0.1))
        ic.segment
    
    # PointProcess still appears here because we have a local ref:
    assert len(pynrn.PointProcess.all_point_processes) == 1
    # ..but it is already destroyed
    with pytest.raises(BaseException):
        pynrn.PointProcess.all_point_processes.values()[0].dur
    
    with pynrn.Context():
        sec = pynrn.Section()
        sec.nseg = 2
        ic = pynrn.IClamp(name="some name")
        assert len(sec.point_processes) == 0
        
        assert ic.name == "some name"
        assert not ic.attached
        
        # Not allowed until attachment
        with pytest.raises(BaseException):
            ic.dur
        with pytest.raises(BaseException):
            ic.dur = 10
            
        ic.attach(sec(0.1))
        assert ic.attached
        assert ic.segment is sec(0.25)
        assert ic.segment.section is sec
        
        # check mangling of keyword names
        assert not hasattr(ic, 'del')
        assert hasattr(ic, 'del_')
        
        assert sec.point_processes == [ic]
        assert sec(0.25).point_processes == [ic]
        assert sec(0.1).point_processes == [ic]
        assert sec(0.75).point_processes == []

        # test pp removal
        sec2 = pynrn.Section()
        pynrn.IClamp(sec2(0.5))._destroy()
        assert len(sec2.point_processes) == 0
        
        # check bad keyword argument
        with pytest.raises(TypeError):
            pynrn.IClamp(sec2(0.2), xxx=5)
            
        # check the failed point process did not persist in the section
        assert len(sec2.point_processes) == 0
        
        sec2 = pynrn.Section()
        ic2 = pynrn.IClamp(sec2(0.2), dur=10, del_=20, amp=5)
        
        assert ic2.attached
        assert ic2.segment is sec2(0.5)
        
        # check init keyword args -> attributes worked
        assert ic2.dur == 10
        assert ic2.del_ == 20
        assert ic2.amp == 5

        # check reattachment
        ic2.attach(sec(0.75))
        ic.attach(sec(0.25))
        
        # check attachment locations are as expected
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
    
        # test detection of lost attachment
        sec = pynrn.Section()
        ic = pynrn.IClamp(sec(0.5))
        assert ic.attached
        assert ic.segment.x == 0.5
        sec._destroy()
        assert ic.section is None
        assert ic.segment is None
        assert not ic.attached
        
    # Another test for reference leak workaround
    # https://www.neuron.yale.edu/phpBB/viewtopic.php?f=2&t=3221
    with pynrn.Context():
        sec = pynrn.Section()
        syn = pynrn.AlphaSynapse(sec(0.5))
        syn.tau

    with pynrn.Context():
        pass
