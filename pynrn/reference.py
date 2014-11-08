import weakref


class FloatVar(float):
    """A float holding information about its source.
    
    This class is used mainly to pass variable references to Vectors. For
    example::
    
        s = Section()
        vm = Vector(record=s(0.5).v)
    """
    def __new__(cls, source, attr, val):
        f = float.__new__(cls, val)
        f._source = weakref.ref(source)
        f._source_name = source.name
        f._attr = attr
        return f

    @property
    def name(self):
        return self._attr
    
    @property
    def source(self):
        return self._source()

    @property
    def _get_ref(self):
        """Reference to the source for this value.
        
        It is not necessary to call this method manually; any class that 
        requires a reference will take care of it. For example, see 
        Vector.__init__.
        """
        source = self._source()
        if source is None:
            raise RuntimeError('Cannot reference "%s" because source object '
                               '"%s" has already been deleted.' % 
                               (self._attr, self._source_name))
        return self._source()._get_ref(self._attr)

    #def __repr__(self):
        #return ("<FloatVar value=%g source=%s.%s at 0x%x>" % 
                #(self, self.source.name, self.name, id(self)))
