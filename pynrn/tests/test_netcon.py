import pytest
import pynrn


def test_netcon():
    with pynrn.Context():
        s = pynrn.Section()
        ns = pynrn.NetStim()
        nc = pynrn.NetCon(s(0.5).v, ns)
        

