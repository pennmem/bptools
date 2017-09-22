import pandas as pd
from bptools.util import FromSeriesMixin


def test_from_series_mixin():
    class Object(FromSeriesMixin):
        def __init__(self, a, b, c):
            self.a = a
            self.b = b
            self.c = c

    series = pd.Series([1, 2, 3], index=['a', 'b', 'c'])
    instance = Object.from_series(series)
    assert instance.a == 1
    assert instance.b == 2
    assert instance.c == 3
