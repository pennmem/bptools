class FromSeriesMixin(object):
    """Utility mixin to add a class method to generate a new instance from a
    :class:`pd.Series`. This provides a single class method :meth:`from_series`.

    """
    @classmethod
    def from_series(cls, s):
        """Create a new instance using the provided series. The series must have
        labels that match arguments provided to the class on instantiation.

        """
        kwargs = {
            attr: value
            for attr, value in s.items()
        }
        return cls(**kwargs)
