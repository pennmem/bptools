import pytest
import numpy as np
import pandas as pd

from bptools.pairs import create_pairs
from bptools.test import datafile


@pytest.mark.parametrize('filename', ['simple_jacksheet.txt', 'R1308T_jacksheet.txt'])
def test_create_pairs(filename):
    pairs = create_pairs(datafile(filename))

    assert 'contact' in pairs.columns
    assert 'pair' in pairs.columns

    combos = np.array([sorted(pair.split('-')) for pair in pairs.pair])
    df = pd.DataFrame({
        'e1': combos[:, 0],
        'e2': combos[:, 1]
    })

    # No contact should be paired with itself
    same = [df.loc[i, 'e1'] == df.loc[i, 'e2'] for i in df.index]
    assert not any(same)

    # No pairs should be repeated
    df = pd.DataFrame({
        'pair': ['-'.join(combo) for combo in combos]
    })
    try:
        assert len(df.pair.unique()) == len(df)
    except AssertionError:
        print(df)
        raise
