import pandas as pd


def read_jacksheet(filename, ignore_ecg=True):
    """Utility function to read a jacksheet.

    Parameters
    ----------
    filename : str
    ignore_ecg : bool
        Omit heart rate channels labeled as ECG/EKG.

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

    if ignore_ecg:
        return js[~js.label.str.startswith('ECG') & ~js.label.str.startswith('EKG')]
    else:
        return js
