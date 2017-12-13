import os.path as osp
from datetime import datetime
from functools import partial
from io import StringIO
from pkg_resources import resource_filename
import re

import pytest

import pandas as pd

from bptools.exc import *
from bptools.odin.config import (
    ElectrodeConfig, make_odin_config, make_config_name, Contact
)
from bptools.odin import cli
from bptools.odin.confgrep import get_odin_config_path
from bptools.odin.config import StimChannel
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
    subject = 'R1308T' if scheme == 'monopolar' else 'R1347D'
    filename = '{:s}_jacksheet.txt'.format(subject)
    prefix = 'R1308T_14JUN2017L0M0STIM' if subject == 'R1308T' else 'R1347D_8DEC2017L0M0STIM'
    output_filename = prefix + '.' + format
    jfile = datafile(filename)

    if scheme == 'monopolar':
        stim_channels = [('LB6', 'LB7'), ('LC7', 'LC8'), ('LB5', 'LB6')]
    else:
        stim_channels = [('LAD8', 'LAD9'), ('LPHCD8', 'LPHCD9'),
                         ('LAHCD9', 'LAHCD10'), ('RAD8', 'RAD9'),
                         ('LOFD8', 'LOFD9'), ('RPHCD8', 'RPHCD9')]

    makeconf = partial(make_odin_config, jfile, prefix, 0.001,
                       stim_channels=stim_channels, scheme=scheme,
                       format=format)

    # Printing to stdout
    makeconf()

    # Saving to a directory
    with tempdir() as path:
        makeconf(path=path)
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
                if not len(line):
                    break

                # We don't really care if the comment section differs
                assert line.split(b'#')[0] == glines[i].split(b'#')[0]

    # Explicitly specifiying leads to include
    good_leads = [n for n in range(1, 4)]
    with tempdir() as path:
        outfile = osp.join(path, output_filename)
        makeconf(path=path, good_leads=good_leads)

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
        assert str(contact) == "Contact(label=x, port=0)"

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

    def test_read_area_file(self):
        filename = resource_filename('bptools.test.data', 'R1347D_area.txt')
        areas = ElectrodeConfig.read_area_file(filename)
        assert len(areas) == 16

        for label in ['ROFD', 'LOFD', 'RAD', 'LAD', 'RAHCD', 'RPHCD', 'RID',
                      'LID', 'RMCD', 'LMCD', 'RPTD', 'LPTD', 'RACD', 'LACD']:
            assert label in areas.label.values

        for n, area in enumerate(areas.area):
            assert area == n + 1

    @pytest.mark.parametrize('scheme', ['bipolar', 'monopolar', 'invalid'])
    @pytest.mark.parametrize('area', [0.5, resource_filename('bptools.test.data', 'simple_area.txt')])
    def test_from_jacksheet(self, scheme, area):
        jfile = datafile('simple_jacksheet.txt')
        subject = "subject"

        if scheme == 'invalid':
            with pytest.raises(AssertionError):
                ElectrodeConfig.from_jacksheet(jfile, subject, scheme)
            return

        ec = ElectrodeConfig.from_jacksheet(jfile, subject, scheme, area=area)
        assert isinstance(ec.contacts[0].port, int)
        assert ec.subject == subject
        assert ec.num_contacts == 37
        assert ec.num_sense_channels == 37 if scheme == 'monopolar' else 35
        assert ec.num_stim_channels == 0

        if area == 0.5:
            for contact in ec.contacts:
                assert contact.area == area
        else:
            areas = ElectrodeConfig.read_area_file(area)
            regex = re.compile(r'(\d*[a-zA-Z]+)')
            for contact in ec.contacts:
                electrode = contact.label[:regex.match(contact.label).end()]
                area_ = areas[areas.label == electrode].area
                assert all(area_ == contact.area)

    @pytest.mark.parametrize('format', ['csv', 'bin'])
    def test_export(self, format):
        jfile = datafile('R1347D_jacksheet.txt')
        scheme = 'bipolar'
        area = 0.001
        ec = ElectrodeConfig.from_jacksheet(jfile, 'R1347D', scheme, area)
        ec.name = '8DEC2017L0M0STIM'

        anodes = ['LAD8', 'LPHCD8', 'LAHCD9', 'RAD8', 'LOFD8', 'RPHCD8']
        cathodes = ['LAD9', 'LPHCD9', 'LAHCD10', 'RAD9', 'LOFD9', 'RPHCD9']
        for args in zip(anodes, cathodes):
            ec.add_stim_channel(*args)

        if format == 'csv':
            with open(datafile("R1347D_8DEC2017L0M0STIM.csv"), 'r') as f:
                ref = f.read().split()
                new = ec.to_csv().split()
                for n, line in enumerate(ref):
                    assert line == new[n]
        else:
            with open(datafile('R1347D_8DEC2017L0M0STIM_bipolar.bin'), 'rb') as f:
                ref = f.read().split(b'|')
                new = ec.to_bin().split(b'|')
                for n, line in enumerate(ref):
                    if len(line) == 0:
                        break
                    assert line == new[n]

    def test_contacts_as_recarray(self):
        ec = ElectrodeConfig.from_jacksheet(datafile("simple_jacksheet.txt"))
        arr = ec.contacts_as_recarray()
        for i, num in enumerate(range(1, 36)):
            assert arr.jack_box_num[i] == num
        assert len(arr.contact_name) == 37
        assert len(arr.description) == 37

    def test_add_stim_channel(self):
        ec = ElectrodeConfig.from_jacksheet(datafile('simple_jacksheet.txt'))
        assert len(ec.stim_channels) == 0

        ec.add_stim_channel('A1', 'A2')
        assert len(ec.stim_channels) == 1
        stim = ec.stim_channels[0]
        assert stim.name == 'A1_A2'
        assert stim.anode == 1
        assert stim.cathode == 2

        with pytest.raises(ContactNotFoundError):
            ec.add_stim_channel('C1', 'A2')

        with pytest.raises(ContactNotFoundError):
            ec.add_stim_channel('A1', 'C2')

        with pytest.raises(ContactNotFoundError):
            ec.add_stim_channel('C1', 'C3')


def test_get_odin_config_path():
    path = get_odin_config_path('R1308T', 'FR1', root=HERE)
    assert path.endswith(osp.join('R1308T', 'behavioral', 'FR1', 'test.bin'))
