import pytest
import pynrn


def test_netcon():
    with pynrn.Context():
        s = pynrn.Section()
        ns1 = pynrn.NetStim()
        ns2 = pynrn.NetStim()
        nc = pynrn.NetCon(s(0.5).v, ns1)
        
        assert nc.source.source is s(0.5)
        assert nc.source.name is 'v'
        assert nc.target is ns1
        assert list(nc.weight) == [0]
        assert nc.delay == 1.
        assert nc.threshold == 10.

        nc.target = ns2
        assert nc.target is ns2

        nc = pynrn.NetCon(s(0.5).v, None)
        assert nc.target is None
        
        nc.target = ns1
        assert nc.target is ns1
        
        nc.target = ns2
        assert nc.target is ns2
        
        nc.target = None
        assert nc.target is None
        
        