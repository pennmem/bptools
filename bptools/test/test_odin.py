import os.path as osp
from datetime import datetime
import pytest

from bptools.odin import make_odin_config, make_config_name
from bptools.test import datafile, tempdir


def test_make_config_name():
    subject = 'R0000M'
    localization = 1
    montage = 0

    now = datetime.now()
    day = now.strftime('%d')
    month = now.strftime('%b').upper()
    year = now.year

    # Stim allowed
    name = make_config_name(subject, localization, montage, True)
    assert name == 'R0000M_{}{}{}L{}M{}STIM'.format(day, month, year,
                                                    localization, montage)

    # Stim forbidden
    name = make_config_name(subject, localization, montage, False)
    assert name == 'R0000M_{}{}{}L{}M{}NOSTIM'.format(day, month, year,
                                                      localization, montage)


@pytest.mark.parametrize('filename', ['R1308T_jacksheet.txt'])
def test_make_odin_config(filename):
    jfile = datafile(filename)

    # Printing to stdout
    make_odin_config(jfile, 'R1308T_NAME', 0.001)

    # Saving to a directory
    with tempdir() as path:
        make_odin_config(jfile, 'R1308T_NAME', 0.001, path)
        assert osp.exists(osp.join(path, 'R1308T_NAME.csv'))
