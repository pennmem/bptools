import os.path as osp
from contextlib import contextmanager
import tempfile
import shutil

HERE = osp.abspath(osp.dirname(__file__))


def datafile(name):
    return osp.join(HERE, 'data', name)


@contextmanager
def tempdir():
    """Create a temporary directory and remove its contents upon completion."""
    d = tempfile.mkdtemp()
    yield d
    try:
        shutil.rmtree(d)
    except:
        pass
