import numpy as np
import pandas as pd
from .jacksheet import read_jacksheet

# Number of channels in one MUX
_ODIN_MUX_CHANNELS = 32


def _mux(n):
    return (n - 1) // _ODIN_MUX_CHANNELS


def _contacts_to_dataframe(jacksheet, contacts):
    """Inner workings of taking a list of contacts and generating a nice,
    human-friendly DataFrame.

    """
    contacts = np.array(contacts)
    labels = [
        jacksheet.loc[contacts[:, n]].label.tolist()
        for n in range(2)
    ]
    pairs = ['-'.join([labels[0][n], labels[1][n]]) for n in range(len(labels[0]))]
    pdf = pd.DataFrame({
        'pair': pairs,
        'label1': labels[0],
        'label2': labels[1],
        'contact1': contacts[:, 0],
        'contact2': contacts[:, 1],
        'mux': [_mux(n) for n in range(len(contacts))],
    })
    return pdf


def _mux_filter(c1, c2):
    if _mux(c1) == _mux(c2):
        return c1, c2
    else:
        return None, None


def create_pairs(jacksheet_filename):
    """Defines bipolar pairs for the Odin ENS given a jacksheet.

    This uses a scheme to live within the constraints of ENS configuration,
    namely that pairs cannot cross a MUX. All neighboring pairs are used, and
    the first and last contacts are also paired.

    Parameters
    ----------
    jacksheet_filename : str
        Path to jacksheet to read.

    Returns
    -------
    pairs : pd.DataFrame

    """
    jacksheet = read_jacksheet(jacksheet_filename)
    groups = jacksheet.electrode.unique()

    contacts = []

    for group in groups:
        # We don't care about heart rate
        if group in ['ECG', 'EKG']:
            continue

        el = jacksheet[jacksheet.electrode == group]
        for i in range(len(el)):
            try:
                # Make adjacent pair
                c1, c2 = _mux_filter(el.index[i], el.index[i + 1])
            except IndexError:
                c1, c2 = _mux_filter(el.index[0], el.index[i])

            for j in range(i):
                if c1 is not None:
                    break
                c1, c2 = _mux_filter(el.index[j], el.index[i])

            if c1 is not None and [c1, c2] not in contacts:
                contacts.append([c1, c2])

    return _contacts_to_dataframe(jacksheet, contacts)
