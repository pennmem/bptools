from bptools.jacksheet import read_jacksheet
from bptools.test import datafile


def test_read_jacksheet():
    filename = datafile('simple_jacksheet.txt')
    js = read_jacksheet(filename)
    assert len(js) == 35
    assert 'electrode' in js.columns
