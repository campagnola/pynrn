class FloatVar(float):
    """A float holding information about its source.
    """
    def __new__(cls, source, attr, val):
        f = float.__new__(cls, val)
        f._source = source
        f._attr = attr
        return f

    @property
    def ref(self):
        """Reference to the source for this value.
        """
        return self._source._get_ref(self._attr)
