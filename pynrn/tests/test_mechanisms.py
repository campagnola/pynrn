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
            assert sec(seg.x+0.01).hh.gk == 0
            seg.hh.gk = i
            assert seg.hh.gk == i
            # check that nearby segments get the same value
            assert sec(seg.x+0.01).hh.gk == i
    
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
        
        # But old segments are no longer valid
        with pytest.raises(RuntimeError):
            midseg.mechanisms
