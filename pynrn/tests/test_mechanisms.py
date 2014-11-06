import pynrn
import numpy as np

def test_distributed():
    with pynrn.Context():
        s = pynrn.Section()
        s.nseg = 10
        s.insert('hh')
        gk = np.linspace(0.1, 0.5, 10)
        s.hh.g_k = gk
        
        for i,seg in enumerate(s):
            assert seg.hh.g_k == gk[i]
    
    