import os.path as osp
from io import StringIO
from contextlib import contextmanager
import pandas as pd


class ParsingError(Exception):
    pass


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

    """
    def __init__(self, filename=None, version="1.2", name="", subject=""):
        self.version = version
        self.name = name
        self.subject = subject

        self.contacts = None  # type: pd.DataFrame
        self.sense_channels = None  # type: pd.DataFrame
        self.stim_channels = None  # type: pd.DataFrame

        # Paths to config files
        self._csv_file = None  # type: str
        self._bin_file = None  # type: str

        if filename is not None:
            self.read_config_file(filename)

    @property
    def num_sense_channels(self):
        """Return the number of configured sense channels."""
        return len(self.sense_channels)

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
                    buf.write(','.join(line) + '\n')
            self.contacts = pd.read_csv(buf, names=[
                'label', 'port', 'port2', 'area', 'description'
            ]).drop('port2', axis=1)

            # Read sense channels
            with buffer() as buf:
                for line in iterlines():
                    buf.write(','.join(line) + '\n')
            self.sense_channels = pd.read_csv(buf, names=[
                'name', 'name2', 'contact', 'ref', 'x', 'description'
            ]).drop(['name2', 'x'], axis=1)

            # Read stim channels
            with buffer() as buf:
                while True:
                    try:
                        line = ','.join([getline()[1] for _ in range(3)])
                        buf.write(line + '\n')
                    except IndexError:
                        break
            self.stim_channels = pd.read_csv(buf, names=[
                'label', 'anode', 'cathode'
            ])


if __name__ == "__main__":
    config = ElectrodeConfig('bptools/test/data/R1308T_14JUN2017L0M0STIM.bin')
    print(config.contacts)
    print(config.sense_channels)
    print(config.stim_channels)
