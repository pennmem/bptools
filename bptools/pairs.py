import numpy as np
import pandas as pd
from .jacksheet import read_jacksheet


def _pair_str(a, b):
    return '-'.join(sorted([a, b]))


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
                continue

            # Last contact
            elif i == len(el) - 1:
                b = el.iloc[-1].label
                if mux_crossed < 0:
                    a = el.iloc[0].label
                else:
                    a = el.iloc[mux_crossed].label

                if a != b:
                    pair = _pair_str(a, b)

                    # Treat the special case of two contacts
                    if pair not in pairs:
                        pairs.append(pair)

            # Adjacent contacts
            else:
                pair = _pair_str(el.iloc[i].label, el.iloc[i + 1].label)
                pairs.append(pair)

    pdf = pd.DataFrame({
        'contact': np.arange(len(pairs)) + 1,
        'pair': pairs
    })
    return pdf
