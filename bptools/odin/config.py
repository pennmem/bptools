import os.path as osp
from io import StringIO
from contextlib import contextmanager
try:
    from typing import List
except ImportError:  # pragma: no cover
    pass
import pandas as pd

from bptools.util import FromSeriesMixin
from bptools.jacksheet import read_jacksheet
from bptools.pairs import create_pairs, create_monopolar_pairs


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


class Contact(FromSeriesMixin, _SlotsMixin):
    """Data about a configured contact."""
    __slots__ = ('label', 'port', 'area', 'description')

    def __init__(self, label, port, area, description):
        self.label = label
        self.port = port
        self.area = area
        self.description = description


class SenseChannel(FromSeriesMixin, _SlotsMixin):
    """Data for a configured sense channel. This consists of two contacts: the
    primary contact and the reference contact.

    """
    __slots__ = ('name', 'contact', 'ref', 'description')

    def __init__(self, name, contact, ref, description):
        self.name = name
        self.contact = contact
        self.ref = ref
        self.description = description


class StimChannel(FromSeriesMixin, _SlotsMixin):
    """Data for a configured stimulation channel."""
    __slots__ = ('name', 'anode', 'cathode')

    def __init__(self, name, anode, cathode):
        self.name = name
        self.anode = anode
        self.cathode = cathode


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

    """
    def __init__(self, filename=None, version="1.2", name="", subject=""):
        self.version = version
        self.name = name
        self.subject = subject

        self.contacts = []  # type: List[Contact]
        self.sense_channels = []  # type: List[SenseChannel]
        self.stim_channels = []  # type: List[StimChannel]

        # Paths to config files
        self._csv_file = None  # type: str
        self._bin_file = None  # type: str

        if filename is not None:
            self.read_config_file(filename)

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
        area : float
            Default surface area to use in mm^2.

        Returns
        -------
        config : ElectrodeConfig

        """
        js = read_jacksheet(filename)
        config = ElectrodeConfig()
        config.subject = subject

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

    def read_config_file(self, filename):
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
                    if len(row) == 1:
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
                ]).drop('port2', axis=1).iterrows()
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


if __name__ == "__main__":  # pragma: no cover
    c1 = Contact('a', 1, 1, '')
    c2 = Contact('a', 1, 1, '')
    print(c1 == c2)
