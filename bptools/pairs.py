import os.path as osp
import json
from collections import namedtuple

import numpy as np
import pandas as pd

from .jacksheet import read_jacksheet

Pair = namedtuple('Pair', ['ch0_label', 'ch1_label', 'pair_label'])

# Number of channels in one MUX
_ODIN_MUX_CHANNELS = 32


def _mux(n):
    return (n - 1) // _ODIN_MUX_CHANNELS


def _contacts_to_dataframe(jacksheet, contacts, monopolar=False):
    """Inner workings of taking a list of contacts and generating a nice,
    human-friendly DataFrame.

    """
    contacts = np.array(contacts)
    col1 = jacksheet.loc[contacts[:, 0]].label.tolist()
    col2 = ['CR'] * len(col1) if all(contacts[:, 1] == 0) else jacksheet.loc[contacts[:, 1]].label.tolist()
    labels = [col1, col2]
    pairs = ['-'.join([labels[0][n], labels[1][n]]) for n in range(len(labels[0]))]
    pdf = pd.DataFrame({
        'pair': pairs,
        'label1': labels[0],
        'label2': labels[1] if not monopolar else 'CR',
        'contact1': contacts[:, 0],
        'contact2': contacts[:, 1] if not monopolar else 0,
        'mux': [_mux(n) for n in range(1, len(contacts) + 1)],
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
        Columns: pair, label1, label2, contact1, contact2, mux

    """
    jacksheet = read_jacksheet(jacksheet_filename)
    groups = jacksheet.electrode.unique()

    contacts = []

    for group in groups:
        el = jacksheet[jacksheet.electrode == group]
        for i in range(len(el)):
            try:
                # Make adjacent pair
                c1, c2 = _mux_filter(el.index[i], el.index[i + 1])
            except IndexError:
                # Pair first and last
                c1, c2 = _mux_filter(el.index[i], el.index[0])

            # Pair distal if nothing else worked
            for j in range(i):
                if c1 is not None:
                    break
                c1, c2 = _mux_filter(el.index[i], el.index[j])

            if c1 is not None and [c1, c2] not in contacts:
                contacts.append([c1, c2])

    return _contacts_to_dataframe(jacksheet, contacts)


def create_monopolar_pairs(jacksheet_filename, common_ref=0):
    """Create 'pairs' that are referenced to a common reference.

    Parameters
    ----------
    jacksheet_filename : str
        Path to jacksheet to read.
    common_ref : int
        Contact number to use as common reference.

    Returns
    -------
    pairs : pd.DataFrame
        See the documentation for :func:`create_pairs` for details.

    """
    assert common_ref >= 0
    assert isinstance(common_ref, int)
    jacksheet = read_jacksheet(jacksheet_filename)
    contacts = [[jacksheet.index[i], common_ref] for i in range(len(jacksheet))]
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


def read_montage_json(montage_path, assume_monopolar=True):
    """Reads pairs.json.  Assumes "consecutive wiring". i.e. when we have e.g.
    130 contacts they are plugged one after another. so based on channel label
    we can determine positional index of that channel For example channel
    labeled 001 will have positional index 0 and channel indexed 122 will have
    positional index 121

    :param str montage_path: path to pairs.json
    :param bool assume_monopolar: specifies whether correspongind electrod
    :rtype: ndarray
    :return: montage recarray with the following columns:
        (contact_name, ch0_label, ch1_label, ch1_idx, ch1_idx)

    """
    with open(montage_path, 'r') as f:
        montage_jn = json.loads(f.read())

    pairs_jn = montage_jn[montage_jn.keys()[0]]['pairs']

    ch0_label = []
    ch1_label = []
    ch0_idx = []
    ch1_idx = []
    pair_label = []

    channel_set = set()
    bp_list = []
    for pair_name, pair_val in pairs_jn.items():
        channel_set.add(int(pair_val['channel_1']))
        channel_set.add(int(pair_val['channel_2']))

        bp_list.append(
            Pair(
                ch0_label=int(pair_val['channel_1']),
                ch1_label=int(pair_val['channel_2']),
                pair_label=pair_name
            )
        )

    channel_array = np.sort(np.array(list(channel_set), dtype=np.int))
    channel_idx_dict = dict(zip(channel_array,np.arange(channel_array.shape[0])))

    if assume_monopolar:
        # we assume that all contacts are present in the electrode configuration
        # file and if the highest contact number is 130 then all 1-130 contacts
        # are listed in the electrode config file we also assume that port
        # numbers are sorted ie 1,2,5,6 is allowed but 5,6,1,2 is not
        for bp in bp_list:

            ch0_idx.append(channel_idx_dict[bp.ch0_label])
            ch1_idx.append(channel_idx_dict[bp.ch1_label])
            ch0_label.append(str(bp.ch0_label).zfill(3))
            ch1_label.append(str(bp.ch1_label).zfill(3))
            pair_label.append(bp.pair_label)
    else:
        # this branch of 'if' statement is valid in one special case: you have
        # fully bipolar electrode config and you generated pairs.json based on
        # it. now you want to compute classifier based on the monopolar
        # recordings - this case is very limited and in practice applies only to
        # debugging scenarios Main assumption is that ch0_idx =
        # int(bp.ch0_label)-1 because in the absence of electrode config file we
        # cannot determine from pairs.json how many contacts were skipped
        for bp in bp_list:

            ch0_idx.append(int(bp.ch0_label)-1)
            ch1_idx.append(int(bp.ch1_label)-1)
            ch0_label.append(str(bp.ch0_label).zfill(3))
            ch1_label.append(str(bp.ch1_label).zfill(3))
            pair_label.append(bp.pair_label)

    montage_dtype = np.dtype([
        ('ch0_idx', '<i8'), ('ch1_idx', '<i8'), ('ch0_label', '|S256'),
        ('ch1_label', '|S256'), ('contact_name', '|S256')
    ])

    e_array = np.recarray((len(ch0_idx),),dtype=montage_dtype)

    for counter, (ch0_idx_, ch1_idx_, ch0_label_, ch1_label_, contact_name_) in enumerate(zip(ch0_idx, ch1_idx, ch0_label, ch1_label, pair_label)):
        e_array[counter]['ch0_idx'] = ch0_idx_
        e_array[counter]['ch1_idx'] = ch1_idx_
        e_array[counter]['ch0_label'] = ch0_label_
        e_array[counter]['ch1_label'] = ch1_label_
        e_array[counter]['contact_name'] = contact_name_

    # sorting by ch0_idx and ch1_idx
    e_array = np.sort(e_array, order=['ch0_idx', 'ch1_idx'])
    return e_array
