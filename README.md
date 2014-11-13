Modern, pythonic API for NEURON.

The goal of pynrn is to provide a clean API for NEURON that avoids many of
the idiosyncracies and common pitfalls encountered when working with NEURON.
This API attempts to preserve most of the vocabulary and workflow of legacy 
NEURON, but does not attempt to provide complete compatibility. 

Features
--------

* Proper python classes for all NEURON object types; no HocObjects.
* Context management: guaranteed separation between subsequent runs.
* Straightorward introspection of NEURON kernel, available mechanisms, 
  and mechanism variables.
* Explicit and automatic creation / deletion of underlying NEURON objects.
* Fully documented, unit-tested API.
* No "ghost" attributes; dir(obj) is always accurate and comprehensive.
* No "_ref_XX" needed to reference range variables.
* All methods are strictly type-checked; no silent failures for incorrectly 
  used methods.
* No segmentation faults for misuse of API (although some pathological cases
  will still crash).
* Pure python (but depends on standard NEURON package).


Incompatibilities with NEURON+Python API
----------------------------------------

* No concept of a section stack (push / pop / cas); sections are always 
  referred to explicitly.
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

* cvode
* Parallel contexts
* documentation for builtin pp / ac classes
* document class incompatibilities in class docstrings
* make sure that anything looking like a drop-in replacement either IS a drop-in
  replacement or will give helpful error messages when used like the original
  API allows
* make properties / methods consistent across classes
    - Segment.section, PointProcess.section, ...
    - Segment.x, PointProcess.loc, ...
* consistent argument checking
* Proper teardown in Context._destroy
    