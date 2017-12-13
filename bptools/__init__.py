from .jacksheet import read_jacksheet
from .pairs import create_pairs, create_monopolar_pairs


class VersionInfo(object):
    def __init__(self, major, minor, patch):
        self.major = major
        self.minor = minor
        self.patch = patch

    def to_tuple(self):
        return self.major, self.minor, self.patch


__version__ = "1.2.1"
version_info = VersionInfo(*__version__.split('.'))
