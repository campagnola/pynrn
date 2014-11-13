# -*- coding: utf-8 -*-
import pytest
from neuron import h

import pynrn


def test_verify():
    with pynrn.Context() as ctx:
        s1 = pynrn.Section()
        s2 = pynrn.Section()
        
        ctx.verify()
        
        sec = h.Section(name="TEST")  # bad!
        del sec
        
        sec = h.Section(name="TEST")  # bad!
        with pytest.raises(RuntimeError):
            ctx.verify()
        
        del sec  # better.
        ctx.verify()
        
        # very bad!
        del s1._Section__nrnobj
        del s1._Section__secref
        with pytest.raises(RuntimeError):
            ctx.verify()
        
        