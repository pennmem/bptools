import pytest
from bptools.jacksheet import read_jacksheet
from bptools.test import datafile


@pytest.mark.parametrize(
    'filename', ['simple_jacksheet.txt', 'R1308T_jacksheet.txt',
                 'R1306E_jacksheet.txt']
)
def test_read_jacksheet(filename):
    jacksheet = datafile(filename)
    js = read_jacksheet(jacksheet)

    if filename.startswith('simple'):
        assert len(js) == 35
    elif filename.startswith('R1308T'):
        assert len(js) == 128
    elif filename.startswith('R1306E'):
        assert len(js) == 122

    assert 'electrode' in js.columns
