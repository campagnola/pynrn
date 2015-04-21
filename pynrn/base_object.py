# -*- coding: utf-8 -*-
import inspect


class BaseObject(object):
    # Contains methods used package-wide for input checking

    def _check_args(self, **kwds):
        """Basic input type-checking.
        
        Keyword arguments are the names of variables to check in the 
        caller's scope. Argument values give a type or tuple of types allowed.
        If float or int types are given, the value is checked by attempting
        to coerce it to float/int.
        
        Example::
        
            self._check_args(
                section=Section,  # argument must be Section instance
                pproc=(PointProcess, type(None)),  # must be PointProcess or None
                x=float))  # succeeds if float(x) is possible
            
        """
        # Danger: accessing locals creates a hidden cache of references
        # https://bugs.python.org/issue6116
        caller_locals = inspect.currentframe().f_back.f_locals
        updates = {}
        for kwd, types in kwds.items():
            if not isinstance(types, tuple):
                types = (types,)
                
            val = caller_locals[kwd]
            
            # If the arg is not already one of the required types, then see if
            # it can be converted.
            if not isinstance(val, types):
                for ctype in (float, int):
                    if ctype in types:
                        try:
                            val = ctype(val)
                            break
                        except Exception:
                            pass
            
            # If no conversions were possible, then raise TypeError
            if not isinstance(val, types):
                names = tuple([typ.__name__ for typ in types])
                if len(names) > 2:
                    names = ', '.join(names[:-1]) + ', or ' + names[-1]
                else:
                    names = ' or '.join(names)
                raise TypeError("Argument %s must be %s (got %s)." % 
                                (kwd, names, type(caller_locals[kwd]).__name__))

    def _check_bounds(self, **kwds):
        """Input boundary checking.
        
        Keyword arguments are the names of variables to check in the 
        caller's scope. Argument values give a tuple of strings that will be 
        evaluated with the checked variable to determine its validity.
        
        Example::
        
            self._check_bounds(
                x=(">= 0", "<= 1"),
                y=("> 0"))
        """
        caller_locals = inspect.currentframe().f_back.f_locals
        for kwd, bounds in kwds.items():
            if not isinstance(bounds, tuple):
                bounds = (bounds,)
            for check in bounds:
                if not eval(kwd + check, {}, caller_locals):
                    bounds = [b.strip() for b in bounds]
                    if len(bounds) < 3:
                        cond = ' and '.join(bounds)
                    else:
                        cond = ', '.join(bounds[:-1]) + ', and ' + bounds[-1]
                    raise ValueError("Argument %s must be %s (got %s)." % 
                                     (kwd, cond, caller_locals[kwd]))

