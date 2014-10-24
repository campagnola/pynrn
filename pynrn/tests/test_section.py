from neuron import h
import pynrn as nrn


def test_section_topology():
    s1 = nrn.Section()
    assert s1.name is None
    assert s1.nchild == 0
    assert s1.parent is None
    assert s1.trueparent is None
    assert s1.root is s1

    s2 = nrn.Section(name="sec2")
    assert s2.name == 'sec2'
    
    s2.connect(s1, 0.5, 0)
    assert s2.parent is s1
    assert s2.trueparent is s1
    assert s2.root is s1
    assert s1.nchild == 1
    assert list(s1.children) == [s2]

    s3 = nrn.Section()
    s3.connect(s2, 0, 0)
    assert s3.parent is s2
    assert s3.trueparent is s1
    assert s3.root is s1
    assert s1.nchild == 1
    assert s2.nchild == 1
    assert list(s2.children) == [s3]

    s4 = nrn.Section()
    s4.connect(s3, 0.5, 1)
    assert s4.root is s1


def test_segments():
    s1 = nrn.Section()
    assert s1.nseg == 1
    assert [s.x for s in s1.segments] == [0.5]
    assert [s.x for s in s1.nodes] == [0, 1]
    
    s1.nseg = 2
    assert s1.nseg == 2
    assert [s.x for s in s1.segments] == [0.25, 0.75]
    assert [s.x for s in s1.nodes] == [0, 0.5, 1]
    
    s1.nseg = 3
    assert s1.nseg == 3
    assert [s.x for s in s1.segments] == [1./6., 3./6., 5./6.]
    assert [s.x for s in s1.nodes] == [0, 1./3., 2./3., 1]
    

def test_destroy():
    s = nrn.Section()
    assert len(list(h.allsec())) == 1
    s._destroy()
    assert len(list(h.allsec())) == 0
    