import os.path as osp
from datetime import datetime
from io import StringIO
import pandas as pd

from bptools.odin import make_odin_config, make_config_name
from bptools.test import datafile, tempdir


def read_sense_config(filename):
    """Utility function to read sense configuration data from the generated
    Odin electrode config CSV file.

    FIXME: consider moving this into :mod:`bptools.odin`.

    """
    with open(filename, 'r') as f:
        # Read until we get to sense channel definition
        line = ''
        while not line.startswith('SenseChannels:'):
            line = f.readline()

        sense_channels = []
        while True:
            line = f.readline()
            if 'Stimulation' in line:
                break
            else:
                sense_channels.append(line)
    csv = StringIO(u"".join(sense_channels))
    config = pd.read_csv(csv, names=['label', 'name', 'c1', 'c2', 'x', 'comment'])
    return config


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


def test_make_odin_config():
    filename = 'R1308T_jacksheet.txt'
    output_filename = 'R1308T_NAME.csv'
    jfile = datafile(filename)

    # Printing to stdout
    make_odin_config(jfile, 'R1308T_NAME', 0.001)

    # Saving to a directory
    with tempdir() as path:
        make_odin_config(jfile, 'R1308T_NAME', 0.001, path)
        outfile = osp.join(path, output_filename)
        assert osp.exists(outfile)

        # Verify that each primary sense channel is only listed once
        config = read_sense_config(outfile)
        assert len(config.c1) == len(config.c1.unique())
        assert all(config.c1 == config.c1.unique())

    # Explicitly specifiying leads to include
    good_leads = [n for n in range(1, 4)]
    with tempdir() as path:
        outfile = osp.join(path, output_filename)
        make_odin_config(jfile, 'R1308T_NAME', 0.001, path, good_leads=good_leads)
        config = read_sense_config(outfile)
        assert len(config) == 2
