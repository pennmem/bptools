import os.path as osp
from datetime import datetime
import pytest
from io import StringIO
import pandas as pd

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
        outfile = osp.join(path, 'R1308T_NAME.csv')
        assert osp.exists(outfile)

        # Verify that each primary sense channel is only listed once
        with open(outfile, 'r') as f:
            # Read until we get to sense channel definition
            line = ''
            while not line.startswith('SenseChannels:'):
                line = f.readline()
            print('done')

            sense_channels = []
            while True:
                line = f.readline()
                if 'Stimulation' in line:
                    break
                else:
                    sense_channels.append(line)

        csv = StringIO("".join(sense_channels))
        config = pd.read_csv(csv, names=['label', 'name', 'c1', 'c2', 'x', 'comment'])
        assert len(config.c1) == len(config.c1.unique())
        assert all(config.c1 == config.c1.unique())
