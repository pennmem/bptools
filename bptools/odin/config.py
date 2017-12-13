from contextlib import contextmanager
from datetime import datetime
from io import StringIO
import os.path as osp
import struct

try:
    from typing import List
except ImportError:  # pragma: no cover
    pass

import numpy as np
import pandas as pd

from bptools.util import FromSeriesMixin, standardize_label
from bptools.jacksheet import read_jacksheet
from bptools.pairs import create_pairs, create_monopolar_pairs


def _num_to_bank_label(num):
    """Convert a channel number to a more human-friendly ENS bank label (e.g.,
    1 -> A-CH01).

    """
    banks = {
        0: 'A',
        1: 'B',
        2: 'C',
        3: 'D'
    }
    bank = banks[(num - 1) // 64]
    # number = num % 64 if bank == 'A' else (num + 1) % 64
    number = num % 64 or 64
    return "{}-CH{:02d}".format(bank, number)


def make_config_name(subject, localization, montage, stim):
    """Create the configuration filename using the standard naming convetion.

    .. todo:: Merge into ElectrodeConfig?

    Parameters
    ----------
    subject : str
    localization : int
    montage : int
    stim : bool

    """
    now = datetime.now()
    name_tmpl = "{subject:s}_{day:02d}{month:s}{year:04d}L{localization:d}M{montage:d}{stim:s}"
    name = name_tmpl.format(**{
        'subject': subject,
        'day': now.day,
        'month': now.strftime('%b'),
        'year': now.year,
        'localization': localization,
        'montage': montage,
        'stim': 'STIM' if stim else 'NOSTIM'
    })
    return name.upper()


def make_odin_config(jacksheet_filename, config_name, default_surface_area,
                     path=None, stim_channels=None, good_leads=None,
                     scheme='bipolar', format='csv'):
    """Create an Odin ENS electrode configuration file.

    .. todo:: Merge into ElectrodeConfig class as a method.

    Parameters
    ----------
    jacksheet_filename : str
        Input jacksheet filename.
    config_name : str
        Configuration file name.
    default_surface_area : float
        Default surface area for electrodes.
    path : str
        Directory to write file to. If None, return as a string.
    stim_channels : List[StimChannel]
        A list of stim channel specifications.
    good_leads : list or None
        Jackbox numbers to use when configuring sense channels. This is usually
        determined from the ``good_leads.txt`` file. When None, use all.
    scheme : str
        Referencing scheme to use (``bipolar`` or ``monopolar``).
    format : str
        Config format to output as (``csv`` or ``bin``).

    Returns
    -------
    Configuration file as a bytes object.

    Notes
    -----
    In the future, jacksheets should optionally include extra annotations such
    as type of electrode (depth, grid, strip) and surface areas.

    """
    assert isinstance(default_surface_area, float)
    assert scheme in ['bipolar', 'monopolar'], "invalid referencing scheme"
    assert format in ['csv', 'bin'], "format must be csv or bin"

    delimiter = b',' if format == 'csv' else b'~'
    newline = b'\n' if format == 'csv' else b'|'

    def iencode(number):
        if format == 'csv':
            return str(number).encode()
        else:
            return struct.pack('<h', number)

    def fencode(number):
        if format == 'csv':
            return "{:.03f}".format(number).encode()
        else:
            return struct.pack('<f', number)

    def delimit(string):
        if format == 'bin':
            return string.replace(',', '~').encode()
        else:
            return string.encode()

    js = read_jacksheet(jacksheet_filename)

    if scheme == 'bipolar':
        pairs = create_pairs(jacksheet_filename)
    elif scheme == 'monopolar':
        pairs = create_monopolar_pairs(jacksheet_filename)

    subject, name = config_name.split('_')

    # Header
    config = [
        delimit("ODINConfigurationVersion:,#1.2#"),
        delimit("ConfigurationName:," + name),
        delimit("SubjectID:," + subject),
        b"Contacts:",
    ]

    # Channel definitions
    for n, row in js.iterrows():
        jbox_num = n
        chan = _num_to_bank_label(jbox_num)
        data = [row.label.encode(), iencode(jbox_num), iencode(jbox_num),
                fencode(default_surface_area),  # FIXME: allow input to set this
                "#Electrode {} jack box {}#".format(chan, jbox_num).encode()]
        config.append(delimiter.join(data))

    # Sense definitions
    config.append(b"SenseChannelSubclasses:")
    config.append(b"SenseChannels:")
    for _, row in pairs.iterrows():
        if good_leads is not None:
            if row.contact1 not in good_leads:
                continue
            if row.contact2 not in good_leads and scheme != "monopolar":
                continue
        data = [row.label1.encode(), row.pair.replace('-', '').encode(),
                iencode(row.contact1), iencode(row.contact2), b'x',
                "#{}#".format(row.pair).encode()]
        config.append(delimiter.join(data))

    # Stim definitions
    config.append(b"StimulationChannelSubclasses:")
    config.append(b"StimulationChannels:")
    if stim_channels is not None:
        for channel in stim_channels:
            entry = channel.config_entry if format == 'csv' else channel.config_entry_bin
            config.append(entry)

    # Footer
    if format == 'csv':
        config.append(b"REF:,0,Common")
    else:
        config.append(b"REF:~\x00\x00~Common")
    config.append(b'EOF')

    if path is not None:
        outfile = osp.join(path, config_name + '.' + format)
        with open(outfile, 'wb') as f:
            f.write(newline.join(config))
            f.write(newline)
    else:
        return newline.join(config)


class _SlotsMixin(object):
    def __eq__(self, other):
        return all([
            getattr(self, slot) == getattr(other, slot)
            for slot in self.__class__.__slots__
        ])

    def __str__(self):
        repr = []
        for slot in self.__class__.__slots__:
            repr.append("{}={}".format(slot, getattr(self, slot)))
        return "<{} {}>".format(self.__class__.__name__, ', '.join(repr))

    def keys(self):
        """Return all the slot names."""
        return [slot for slot in self.__class__.__slots__]


class Contact(FromSeriesMixin, _SlotsMixin):
    """Data about a configured contact."""
    __slots__ = ('label', 'port', 'area', 'description')

    def __init__(self, label, port, area, description):
        self.label = label  # type: str
        self.port = port  # type: int
        self.area = area  # type: float
        self.description = description  # type: str


class SenseChannel(FromSeriesMixin, _SlotsMixin):
    """Data for a configured sense channel. This consists of two contacts: the
    primary contact and the reference contact.

    """
    __slots__ = ('name', 'contact', 'ref', 'description')

    def __init__(self, name, contact, ref, description):
        self.name = name  # type: str
        self.contact = contact  # type: int
        self.ref = ref  # type: int
        self.description = description  # type: str

    @property
    def label(self):
        return self.name


class StimChannel(FromSeriesMixin, _SlotsMixin):
    """Data for a configured stimulation channel."""
    __slots__ = ('name', 'anode', 'cathode')

    def __init__(self, name, anode, cathode):
        self.name = name  # type: str
        self.anode = anode  # type: int
        self.cathode = cathode  # type: int

    @property
    def label(self):
        return self.name

    @property
    def config_entry(self):
        """Returns the CSV config file representation of this stim channel.

        Returns
        -------
        bytes

        """
        return '\n'.join([
            'StimChannel:,{:s},x,# #'.format(self.name),
            'Anodes:,{:d},#'.format(self.anode),
            'Cathodes:,{:d},#'.format(self.cathode)
        ]).encode()

    @property
    def config_entry_bin(self):
        """Returns the binary config file representation of this stim channel.

        Returns
        -------
        bytes

        """
        return b'|'.join([
            'StimChannel:~{:s}~x~# #'.format(self.name).encode(),
            b'Anodes:~' + struct.pack('<h', self.anode) + b'~#',
            b'Cathodes:~' + struct.pack('<h', self.cathode) + b'~#'
        ])


class ElectrodeConfig(object):
    """Representation of OdinLib electrode configuration files.

    Parameters
    ----------
    filename : str
        Path to Odin binary or CSV configuration file. Both must be present in
        the same directory.
    version : str
        Odin config version number
    name : str
        Name given to config file (alphanumeric only)
    subject : str
        Subject ID

    Attributes
    ----------
    contacts : list of :class:`Contact`
        Contact labels and numbers.
    sense_channels : list of :class:`SenseChannel`
        Configured sense channels.
    stim_channels : list of :class:`StimChannel`
        Configured stimulation channels.

    Notes
    -----
    All ``x_as_recarray`` methods return a recarray with the following columns:

    * jack_box_num - int
    * contact_name - str
    * description - str

    """
    def __init__(self, filename=None, version="1.2", name="", subject=""):
        self.version = version  # type: str
        self.name = name  # type: str
        self.subject = subject  # type: str

        self.contacts = []  # type: List[Contact]
        self.sense_channels = []  # type: List[SenseChannel]
        self.stim_channels = []  # type: List[StimChannel]

        # Paths to config files
        self._csv_file = None  # type: str
        self._bin_file = None  # type: str

        if filename is not None:
            self.read_config_file(filename)

        # dtype for when exporting as a recarray
        # Naming conventions here differ for backwards compatibility with
        # Ramulator.
        self._recarray_dtype = np.dtype([
            ('jack_box_num', '<i8'), ('contact_name', '|S256'),
            ('description', '|S256')
        ])

    def __str__(self):
        return "<ElectrodeConfig(num contacts={}, num sense channels={}, num stim channels={}>".format(
            len(self.contacts), len(self.sense_channels), len(self.stim_channels)
        )

    @property
    def num_contacts(self):
        """Return the number of configured contacts."""
        return len(self.contacts)

    @property
    def num_sense_channels(self):
        """Return the number of configured sense channels."""
        return len(self.sense_channels)

    @property
    def num_stim_channels(self):
        """Return the number of configured stim channels."""
        return len(self.stim_channels)

    @staticmethod
    def read_area_file(filename):
        """Read a file that maps electrode labels to surface areas (see notes
        below).

        Parameters
        ----------
        filename : str
            Path to file

        Returns
        -------
        pd.DataFrame
            A dataframe containing the columns ``label`` and ``area``.

        Notes
        -----
        Contact surface areas will be read in from the file with the following
        format::

            <electrode label 1> <surface area in mm^2>
            <electrode label 2> <surface area in mm^2>

        Electrode labels are everything preceding the specific contact number,
        so ``LA1``, ``LA2``, etc. would use ``LA`` as the electrode label. This
        assumes that in electrodes that combine contacts of different sizes that
        each uniquely sized contact has a different labeling prefix. In other
        words, if the ``LA`` lead contains both micro and macro contacts, the
        jacksheet should be updated to label the micros with something like
        ``uLA`` so that the surface area file could contain lines like::

            LA 1
            uLA 0.01

        """
        with open(filename, 'r') as f:
            lines = [line.split() for line in f.read().split('\n') if len(line)]
            areas = []
            for label, area in lines:
                areas.append({'label': label.strip(), 'area': float(area)})
            return pd.DataFrame(areas)

    @classmethod
    def from_jacksheet(cls, filename, subject="", scheme='bipolar', area=0.5):
        """Create a new :class:`ElectrodeConfig` instance from a jacksheet.

        Parameters
        ----------
        filename : str
            Path to jacksheet file.
        subject : str
            Subject ID
        scheme : str
            Referencing scheme to use (``bipolar`` or ``monopolar``).
        area : float or str
            Default surface area to use in mm^2 when a float or a file that
            maps electrode labels to surface areas (see :meth:`read_area_file`
            for file format details).

        Returns
        -------
        config : ElectrodeConfig

        """
        js = read_jacksheet(filename)
        config = ElectrodeConfig()
        config.subject = subject

        if isinstance(area, str):
            areas = cls.read_area_file(area)

        config.contacts = [
            Contact.from_series(s)
            for _, s in pd.DataFrame({
                'label': js.label,
                'port': js.index,
                'area': [area] * len(js),
                'description': ['Jackbox number {}'.format(n) for n in js.index]
            }).iterrows()
        ]

        if scheme == 'bipolar':
            pairs = create_pairs(filename)
        elif scheme == 'monopolar':
            pairs = create_monopolar_pairs(filename)
        else:
            raise AssertionError("Unrecognized referencing scheme")

        config.sense_channels = [
            SenseChannel.from_series(s)
            for _, s in pd.DataFrame({
                'name': pairs.label1 + "CR" if scheme == 'monopolar' else pairs.label1 + pairs.label2,
                'contact': pairs.contact1,
                'ref': pairs.contact2,
                'description': pairs.pair
            }).iterrows()
        ]

        return config

    def read_config_file(self, filename, standardize_labels=False):
        """Populate the instance from an Odin electrode configuration file.

        Parameters
        ----------
        filename : str
            Path to Odin binary or CSV config file.

        """
        if filename.endswith(".bin"):
            self._csv_file = filename.replace(".bin", ".csv")
            self._bin_file = filename
        elif filename.endswith(".csv"):
            self._csv_file = filename
            self._bin_file = filename.replace(".bin", ".csv")
        else:
            raise RuntimeError("Config file must end with .bin or .csv")

        assert osp.exists(self._csv_file), "CSV electrode config file must exist!"
        assert osp.exists(self._bin_file), "binary electrode config file must exist!"

        with open(self._csv_file, 'r') as f:
            getline = lambda: f.readline().strip().split(',')

            def iterlines():
                while True:
                    row = getline()
                    if "Subclasses:" in ','.join(row):
                        getline()
                        raise StopIteration
                    yield row

            @contextmanager
            def buffer():
                buf = StringIO()
                yield buf
                buf.seek(0)

            # Read header information
            self.version = getline()[1].split('#')[1]
            self.name = getline()[1]
            self.subject = getline()[1]

            # Next line is 'Contacts:'
            getline()

            # Read contacts
            with buffer() as buf:
                for line in iterlines():
                    buf.write(','.join(line) + u'\n')
            self.contacts = [
                Contact.from_series(s)
                for _, s in pd.read_csv(buf, names=[
                    'label', 'port', 'port2', 'area', 'description'
                ], index_col=False).drop('port2', axis=1).iterrows()
            ]

            # Read sense channels
            with buffer() as buf:
                for line in iterlines():
                    buf.write(','.join(line) + u'\n')
            self.sense_channels = [
                SenseChannel.from_series(s)
                for _, s in pd.read_csv(buf, names=[
                    'primary_name', 'name', 'contact', 'ref', 'x', 'description'
                ]).drop(['primary_name', 'x'], axis=1).iterrows()
            ]

            # Read stim channels
            with buffer() as buf:
                while True:
                    try:
                        line = ','.join([getline()[1] for _ in range(3)])
                        buf.write(line + u'\n')
                    except IndexError:
                        break
            self.stim_channels = [
                StimChannel.from_series(s)
                for _, s in pd.read_csv(buf, names=[
                    'name', 'anode', 'cathode'
                ]).iterrows()
            ]

            # Optionally standardize labels for contacts, sense channels, and stim channels
            if standardize_labels:
                for contact in self.contacts:
                    contact.label = standardize_label(contact.label)
                for sense_channel in self.sense_channels:
                    sense_channel.name = standardize_label(sense_channel.name)
                for stim_channel in self.stim_channels:
                    stim_channel.name = standardize_label(stim_channel.name)

    def to_csv(self, outfile=None):
        """Export as an Odin CSV electrode configuration file.

        Parameters
        ----------
        outfile : str
            Name of the output file.

        Returns
        -------
        ``str`` if outfile is ``None`` else ``None`` and writes to ``outfile``.

        Notes
        -----
        For now, this only works if the configuration was generated from an
        existing CSV file.

        """
        assert self._csv_file is not None, "TODO: implement more general to_csv"

        with open(self._csv_file, 'r') as f:
            config = f.read()

        if outfile is None:
            return config
        else:
            with open(outfile, 'w') as f:
                f.write(config)

    def contacts_as_recarray(self):
        """Return the monopolar contacts as a recarry.

        This method exists for Ramulator compatibility.

        """
        arr = np.recarray((len(self.contacts),), dtype=self._recarray_dtype)

        for i, contact in enumerate(self.contacts):
            arr[i]['jack_box_num'] = int(contact.port)
            arr[i]['contact_name'] = str(contact.label)
            # Not using surface area anymore because not used by Ramulator
            # arr[i]['surface_area'] = float(contact.area)
            arr[i]['description'] = str(contact.description)

        return arr

    def sense_channels_as_recarray(self):
        """Return the sense channels as a recarray.

        This method exists for Ramulator compatibility.

        """
        arr = np.recarray((len(self.sense_channels),), dtype=self._recarray_dtype)

        for i, chan in enumerate(self.sense_channels):
            arr[i]['jack_box_num'] = int(chan.contact)
            arr[i]['contact_name'] = str(chan.name)
            arr[i]['description'] = str(chan.name)

        return arr


if __name__ == "__main__":  # pragma: no cover
    c1 = Contact('a', 1, 1, '')
    c2 = Contact('a', 1, 1, '')
    print(c1 == c2)
