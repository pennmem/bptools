import pytest
from bptools.jacksheet import read_jacksheet
from bptools.test import datafile


@pytest.mark.parametrize(
    'filename', ['simple_jacksheet.txt', 'R1308T_jacksheet.txt',
                 'R1306E_jacksheet.txt']
)
@pytest.mark.parametrize('ignore_ecg', [True, False])
@pytest.mark.parametrize('standardize_labels', [True, False])
def test_read_jacksheet(filename, ignore_ecg, standardize_labels):
    jacksheet = datafile(filename)
    js = read_jacksheet(jacksheet, ignore_ecg=ignore_ecg, standardize_labels=standardize_labels)

    if filename.startswith('simple'):
        assert len(js) == 35
    elif filename.startswith('R1308T'):
        assert len(js) == 128 if not ignore_ecg else 126
    elif filename.startswith('R1306E'):
        assert len(js) == 122 if not ignore_ecg else 120
        labels = js.label.values
        assert ('2RD1' in labels) if standardize_labels else ('2Rd1' in labels)

    assert 'electrode' in js.columns
