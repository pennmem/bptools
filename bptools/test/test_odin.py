import os.path as osp
from datetime import datetime
from io import StringIO
from pkg_resources import resource_filename

import pytest

import pandas as pd

from bptools.odin.config import (
    ElectrodeConfig, make_odin_config, make_config_name, Contact
)
from bptools.odin import cli
from bptools.odin.confgrep import get_odin_config_path
from bptools.test import datafile, tempdir, HERE


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


@pytest.mark.parametrize('scheme', ['bipolar', 'monopolar'])
@pytest.mark.parametrize('format', ['csv', 'bin', 'txt'])
def test_make_odin_config(scheme, format):
    filename = 'R1308T_jacksheet.txt'
    prefix = 'R1308T_14JUN2017L0M0STIM'
    output_filename = prefix + '.csv'
    jfile = datafile(filename)

    if format == 'txt':
        with pytest.raises(AssertionError):
            make_odin_config(jfile, prefix, 0.001, format=format)
        return

    # Printing to stdout
    make_odin_config(jfile, prefix, 0.001, scheme=scheme, format=format)

    # Saving to a directory
    with tempdir() as path:
        make_odin_config(jfile, prefix, 0.001, path, scheme=scheme, format=format)
        outfile = osp.join(path, output_filename)
        assert osp.exists(outfile)

        # Verify that each primary sense channel is only listed once
        if format == 'csv':
            config = read_sense_config(outfile)
            assert len(config.c1) == len(config.c1.unique())
            assert all(config.c1 == config.c1.unique())
        elif format == 'bin':
            reffile = '{}_{}.bin'.format(prefix, scheme)
            with open(resource_filename('bptools.test.data', reffile), 'rb') as ref:
                with open(outfile, 'rb') as gen:
                    rlines = ref.read()
                    glines = gen.read()

            rlines = rlines.split(b'|')
            glines = glines.split(b'|')
            for i, line in enumerate(rlines):
                # We don't really care if the comment section differs
                assert line.split(b'#')[0] == glines[i].split(b'#')[0]

    # Explicitly specifiying leads to include
    good_leads = [n for n in range(1, 4)]
    with tempdir() as path:
        outfile = osp.join(path, output_filename)
        make_odin_config(jfile, prefix, 0.001, path, good_leads=good_leads,
                         scheme=scheme, format=format)

        if format == 'csv':
            config = read_sense_config(outfile)
            if scheme == 'bipolar':
                assert len(config) == 2
            else:
                assert len(config) == 3
        elif format == 'bin':
            pass  # FIXME


def test_cli():
    args = [
        '--subject=R1308T',
        '--stim',
        '--rhino-root={}'.format(osp.join(HERE))
    ]
    cli.main(args=args)


class TestSlotsMixin:
    def test_str(self):
        contact = Contact("x", 0, 1, "description")
        assert str(contact) == "<Contact label=x, port=0, area=1, description=description>"

    def test_keys(self):
        contact = Contact("x", 0, 1, "description")
        assert contact.keys() == ['label', 'port', 'area', 'description']


class TestElectrodeConfig:
    @pytest.mark.parametrize('extension', ['.csv', '.bin', '.txt'])
    def test_read_config_file(self, extension):
        ec = ElectrodeConfig()
        filename = 'R1308T_14JUN2017L0M0STIM' + extension

        if extension == '.txt':
            with pytest.raises(RuntimeError):
                ec.read_config_file(datafile(filename))
            return

        ec.read_config_file(datafile(filename))

        assert ec.subject == 'R1308T'
        assert ec.version == '1.2'
        assert ec.name == '14JUN2017L0M0STIM'

        assert all([ch.name == ch.label for ch in ec.sense_channels])
        assert all([ch.name == ch.label for ch in ec.stim_channels])

        assert len(ec.contacts) == 126
        assert len(ec.sense_channels) == 126
        assert len(ec.stim_channels) == 3

        ec2 = ElectrodeConfig(datafile(filename))
        assert ec.subject == ec2.subject
        assert ec.version == ec2.version
        assert ec.name == ec2.name
        assert all([ec.contacts[i] == ec2.contacts[i] for i in range(len(ec.contacts))])
        assert all([ec.sense_channels[i] == ec2.sense_channels[i] for i in range(len(ec.sense_channels))])
        assert all([ec.stim_channels[i] == ec2.stim_channels[i] for i in range(len(ec.stim_channels))])

    @pytest.mark.skip(reason='Fails for monopolar')
    @pytest.mark.parametrize('odin,jacksheet,scheme', [
        ('R1306E_22SEP2017L0M0NOSTIM.csv', 'R1306E_jacksheet.txt', 'monopolar'),]
    )
    def test_creation_methods(self, odin, jacksheet, scheme):
        ec = ElectrodeConfig(filename=datafile(odin))
        ec2 = ElectrodeConfig.from_jacksheet(datafile(jacksheet), scheme=scheme)

        assert len(ec.contacts) == len(ec2.contacts)
        assert len(ec.sense_channels) == len(ec2.sense_channels)

        # n.b., stim channels shouldn't be defined for ec2
        assert len(ec2.stim_channels) == 0

        for i, _ in enumerate(ec.contacts):
            assert ec.contacts[i].label == ec2.contacts[i].label
            assert ec.contacts[i].port == ec2.contacts[i].port

        for i, _ in enumerate(ec.sense_channels):
            assert ec.sense_channels[i].name == ec2.sense_channels[i].name
            assert ec.sense_channels[i].contact == ec2.sense_channels[i].contact
            assert ec.sense_channels[i].ref == ec2.sense_channels[i].ref

    @pytest.mark.parametrize('scheme', ['bipolar', 'monopolar', 'invalid'])
    def test_from_jacksheet(self, scheme):
        jfile = datafile('simple_jacksheet.txt')
        subject = "subject"

        if scheme == 'invalid':
            with pytest.raises(AssertionError):
                ElectrodeConfig.from_jacksheet(jfile, subject, scheme)
            return

        ec = ElectrodeConfig.from_jacksheet(jfile, subject, scheme)
        assert isinstance(ec.contacts[0].port, int)
        assert ec.subject == subject
        assert ec.num_contacts == 35
        assert ec.num_sense_channels == 35 if scheme == 'monopolar' else 34
        assert ec.num_stim_channels == 0

    def test_to_csv(self, tmpdir):
        basename = "R1308T_14JUN2017L0M0STIM.csv"
        filename = datafile(basename)
        ec = ElectrodeConfig(filename)
        stringy = ec.to_csv()

        with open(filename, 'r') as original:
            assert stringy == original.read()

        outfile = str(tmpdir.join(basename))
        ec.to_csv(outfile=outfile)

        with open(filename, 'r') as original:
            with open(outfile, 'r') as new:
                assert new.read() == original.read()

    def test_contacts_as_recarray(self):
        ec = ElectrodeConfig.from_jacksheet(datafile("simple_jacksheet.txt"))
        arr = ec.contacts_as_recarray()
        for i, num in enumerate(range(1, 36)):
            assert arr.jack_box_num[i] == num
        assert len(arr.contact_name) == 35
        assert len(arr.description) == 35


def test_get_odin_config_path():
    path = get_odin_config_path('R1308T', 'FR1', root=HERE)
    assert path.endswith(osp.join('R1308T', 'behavioral', 'FR1', 'test.bin'))
