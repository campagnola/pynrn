Modern, pythonic API for NEURON.

The goal of pynrn is to provide a clean API for NEURON that avoids many of
the idiosyncracies and common pitfalls encountered when working with NEURON.
This API attempts to preserve most of the vocabulary and workflow of legacy 
NEURON, but does not attempt to provide complete compatibility. 

Features
--------

* Proper python classes for all NEURON object types
* Context management: guaranteed separation between subsequent runs.
* Straightorward introspection of NEURON kernel, available mechanisms, 
  and mechanism variables
* Explicit and automatic creation / deletion of underlying NEURON objects
* Fully documented, unit-tested API
* No HocObjects
* Pure python (but depends on standard neuron package)
* No "ghost" attributes; dir(obj) is always accurate and comprehensive
* No "segment._ref_XX" needed; just use "segment.XX"


Incompatibilities with NEURON+Python API
----------------------------------------

* There is no equivalent "neuron.h" namespace; most of these features are 
  wrapped into classes.
    * For running simulations, see Context.init, .run, .advance, .t, .celsius,
      .dt, ...
* The NEURON API allows distributed mechanism variables to be accessed three
  different ways::
      
      section.gk_hh
      section(0.5).gk_hh
      section(0.5).hh.gk
      
  In pynrn only the last form is allowed. 
* SectionRef is gone; these features are now wrapped into Section.
    * See Section.nchild, .child, .children, .parent, .trueparent, and .root
* MechanismType and MechanismStandard are gone; these features are now wrapped 
  into Mechanism.
    * See Mechanism.is_netcon_target, .has_net_event, .internal_type, .global,
      .parameter, .assigned, and .state.
    * See Mechanism.all_mechanism_types for a listing of all available
      mechanisms.
    
Todo
----

* detach / reattach point processes
* remove dist mechanisms
* netcon
* documentation for builtin pp / ac classes
* morphology
* Parallel contexts
* extracellumar mechanisms
