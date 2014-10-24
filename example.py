import pynrn as nrn
import numpy as np


sim = nrn.Context()

cell = nrn.Section()
cell.insert('hh')

vm = nrn.Vector(cell(0.5).v)
sim.run(dt=0.025, celsius=25, tstop=20)

vm = vm.asarray()

# destroy all objects created in this context, allowing another to begin
sim.finish()

