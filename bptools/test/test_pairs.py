import pytest

from bptools.pairs import create_pairs
from bptools.test import datafile


@pytest.mark.parametrize('filename', ['simple_jacksheet.txt'])
def test_create_pairs(filename):
    pairs = create_pairs(datafile(filename))

    assert 'contact' in pairs.columns
    assert 'pair' in pairs.columns
