import pytest
from bptools.jacksheet import read_jacksheet
from bptools.test import datafile


@pytest.mark.parametrize(
    'filename', ['simple_jacksheet.txt', 'R1308T_jacksheet.txt',
                 'R1306E_jacksheet.txt']
)
@pytest.mark.parametrize('ignore_ecg', [True, False])
def test_read_jacksheet(filename, ignore_ecg):
    jacksheet = datafile(filename)
    js = read_jacksheet(jacksheet, ignore_ecg=ignore_ecg)

    if filename.startswith('simple'):
        assert len(js) == 35
    elif filename.startswith('R1308T'):
        assert len(js) == 128 if not ignore_ecg else 126
    elif filename.startswith('R1306E'):
        assert len(js) == 122 if not ignore_ecg else 120

    assert 'electrode' in js.columns
