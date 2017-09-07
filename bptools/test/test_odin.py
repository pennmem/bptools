import pytest

from bptools.odin import make_odin_config
from bptools.test import datafile


@pytest.mark.parametrize('filename', ['R1308T_jacksheet.txt'])
def test_make_odin_config(filename):
    output = make_odin_config(datafile(filename), 'test', 'R0000X')
    print(output)
