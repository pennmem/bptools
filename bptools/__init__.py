from collections import namedtuple

from .jacksheet import read_jacksheet
from .pairs import create_pairs, create_monopolar_pairs

__version__ = "1.1.2"

version_info = namedtuple("VersionInfo", "major, minor, patch")(*__version__.split('.'))
