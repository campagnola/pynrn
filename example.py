import pynrn as nrn
import numpy as np


sim = nrn.Context()

cell = nrn.Section()
cell.insert('hh')

ic = nrn.IClamp(0.5, cell)

vm = nrn.Vector(cell(0.5).v)
gk = nrn.Vector(cell(0.5).hh.gk)

sim.run(dt=0.025, celsius=25, tstop=20)

vm = vm.asarray()
gk = gk.asarray()

# destroy all objects created in this context, allowing another to begin
#sim.finish()

