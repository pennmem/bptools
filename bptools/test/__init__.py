import os.path as osp
from contextlib import contextmanager
import tempfile
import shutil


def datafile(name):
    return osp.join(osp.abspath(osp.dirname(__file__)), 'data', name)


@contextmanager
def tempdir():
    """Create a temporary directory and remove its contents upon completion."""
    d = tempfile.mkdtemp()
    yield d
    try:
        shutil.rmtree(d)
    except:
        pass
