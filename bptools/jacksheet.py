import pandas as pd
from bptools.util import standardize_label
from functools import reduce


def read_jacksheet(filename, ignore_labels=['EKG', 'ECG'], standardize_labels=False):
    """Utility function to read a jacksheet.

    Parameters
    ----------
    filename : str
    standarize_labels: bool
        Standarize contact labels when reading in the jacksheet
    ignore_labels: list or tuple
        Labels to ignore from jacksheet

    Returns
    -------
    pd.DataFrame

    Notes
    -----
    Columns in the returned :class:`pd.DataFrame`:

    * ``label``: contact labels
    * ``electrode``: electrode the contact resides on (same as ``label``
      without the number)

    The index is the jackbox number.

    """

    df = pd.read_csv(filename, index_col=0, names=['label'], sep='\s+')

    electrodes = df.label.str.extract(r'(\d*[a-zA-Z]+)', expand=True) \
        .rename(columns={0: 'electrode'})
    js = pd.concat([df, electrodes], axis=1)

    if standardize_labels:
        js['label'] = js['label'].apply(standardize_label)

    if ignore_labels:
        js = js[reduce(lambda a, b: a & b,[~js.label.str.startswith(label) for label in ignore_labels])]

    return js
