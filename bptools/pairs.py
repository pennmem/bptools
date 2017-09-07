import numpy as np
import pandas as pd
from .jacksheet import read_jacksheet


def _pair_str(a, b):
    return '-'.join(sorted([a, b], key=lambda s: int(''.join([n for n in s if n.isdigit()]))))


def create_pairs(jacksheet_filename, mux_channels=32):
    """Defines bipolar pairs for the Odin ENS given a jacksheet.

    This uses a scheme to live within the constraints of ENS configuration,
    namely that pairs cannot cross a MUX. All neighboring pairs are used, and
    the first and last contacts are also paired.

    Parameters
    ----------
    jacksheet_filename : str
        Path to jacksheet to read.

    Keyword Arguments
    -----------------
    mux_channels : int
        Number of channels contained in a MUX (32 for the Odin ENS).

    Returns
    -------
    pairs : pd.DataFrame

    """
    jacksheet = read_jacksheet(jacksheet_filename)
    groups = jacksheet.electrode.unique()

    pairs = []
    contacts = []
    mux = 0

    for group in groups:
        mux_crossed = -1

        el = jacksheet[jacksheet.electrode == group]
        for i in range(len(el)):
            mux += 1

            # MUX crossing
            if mux % mux_channels == 0 and mux != 0 and i != 0:
                mux_crossed = i + 1
                pair = _pair_str(el.iloc[i].label, el.iloc[0].label)
                if pair not in pairs:
                    pairs.append(pair)
                    contacts.append([el.index[i], el.index[0]])
                continue

            # Last contact
            elif i == len(el) - 1:
                b = el.iloc[-1].label
                bi = len(el) - 1
                if mux_crossed < 0:
                    a = el.iloc[0].label
                    ai = 0
                else:
                    a = el.iloc[mux_crossed].label
                    ai = mux_crossed

                if a != b:
                    pair = _pair_str(a, b)

                    # Treat the special case of two contacts
                    if pair not in pairs:
                        pairs.append(pair)
                        contacts.append([el.index[ai], el.index[bi]])

            # Adjacent contacts
            else:
                pair = _pair_str(el.iloc[i].label, el.iloc[i + 1].label)
                pairs.append(pair)
                contacts.append([el.index[i], el.index[i + 1]])

    labels = np.array([pair.split('-') for pair in pairs])
    contacts = np.array(contacts)
    pdf = pd.DataFrame({
        'pair': pairs,
        'label1': labels[:, 0],
        'label2': labels[:, 1],
        'contact1': contacts[:, 0],
        'contact2': contacts[:, 1],
    })
    return pdf
