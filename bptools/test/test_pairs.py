import pytest
import numpy as np
import pandas as pd

from bptools.pairs import create_pairs
from bptools.test import datafile


@pytest.mark.parametrize('filename', ['simple_jacksheet.txt', 'R1308T_jacksheet.txt'])
def test_create_pairs(filename):
    pairs = create_pairs(datafile(filename))

    assert 'pair' in pairs.columns
    assert 'label1' in pairs.columns
    assert 'label2' in pairs.columns
    assert 'contact1' in pairs.columns
    assert 'contact2' in pairs.columns
    assert 'mux' in pairs.columns

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
    assert len(df.pair.unique()) == len(df)

    # Labels should match pairs
    for n, row in pairs.iterrows():
        assert row.label1 in row.pair
        assert row.label2 in row.pair


def test_no_mux_crossing():
    pairs = create_pairs(datafile('mux_test_jacksheet.csv'))
    for pair in pairs.pair:
        if 'A' in pair:
            assert 'B' not in pair
        if 'B' in pair:
            assert 'A' not in pair
