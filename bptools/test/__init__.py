import os.path as osp


def datafile(name):
    return osp.join(osp.abspath(osp.dirname(__file__)), 'data', name)
