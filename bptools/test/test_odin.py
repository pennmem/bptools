import os.path as osp
import pytest

from bptools.odin import make_odin_config
from bptools.test import datafile, tempdir


@pytest.mark.parametrize('filename', ['R1308T_jacksheet.txt'])
def test_make_odin_config(filename):
    jfile = datafile(filename)
    make_odin_config(jfile, 'test', 'R1308T')

    with tempdir() as path:
        make_odin_config(jfile, 'test', 'R1308T', path)
        assert osp.exists(osp.join(path, 'R1308T_test.csv'))

