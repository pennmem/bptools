import os.path as osp
import json

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
                # Pair first and last
                c1, c2 = _mux_filter(el.index[i], el.index[0])

            for j in range(i):
                if c1 is not None:
                    break
                c1, c2 = _mux_filter(el.index[j], el.index[i])

            if c1 is not None and [c1, c2] not in contacts:
                contacts.append([c1, c2])

    return _contacts_to_dataframe(jacksheet, contacts)


def pairs_to_json(pairs, subject, path):
    """Convert a pairs :class:`pd.DataFrame` to a ``pairs.json`` file (with
    coordinates omitted).

    Parameters
    ----------
    pairs : pd.DataFrame
    subject : str
        Subject ID.
    path : str
        Path to write ``pairs.json`` to.

    Notes
    -----
    Currently, several other fields are omitted, e.g., electrode type.

    """
    pd = {}
    for _, row in pairs.iterrows():
        pd[row.pair] = {
            'atlases': {},
            'channel_1': row.contact1,
            'channel_2': row.contact2,
            'code': row.pair,
            'id': row.pair,
            'is_explicit': False,
            'is_stim_only': False,
            'type_1': 'U',
            'type_2': 'U'
        }

    with open(osp.join(path, 'pairs.json'), 'w') as f:
        out = {
            subject: {
                'pairs': pd
            },
            'code': subject,
        }
        f.write(json.dumps(out))


def write_pairs(pairs, filename, **kwargs):
    """Write pairs to a file.

    Parameters
    ----------
    pairs : pd.DataFrame
    filename : str
        File to write. File type is determined by the extension. Accepted file
        extensions are: ``.csv``, ``.json``. If saving as JSON, pairs will be
        saved in a minimal ``pairs.json`` format which excludes coordinates.

    Keyword arguments
    -----------------
    kwargs : dict
        Keyword arguments to pass to pandas ``to_xyz`` functions when writing
        formats other than JSON. If writing ``pairs.json``, a ``subject``
        keyword argument is also required.
    subject : str
        Subject ID.

    Raises
    ------
    ValueError when subject kwarg is missing (for writing ``pairs.json``) or an
    unsupported extension is used.

    """
    subject = kwargs.pop('subject', None)
    if filename.endswith('.csv'):
        pairs.to_csv(filename, **kwargs)
    elif filename.endswith('.json'):
        if subject is None:
            raise ValueError("Subject ID is required for writing pairs.json")
        path = osp.split(filename)[0]
        pairs_to_json(pairs, subject, path)
    else:
        raise ValueError("Unsupported tile type")
