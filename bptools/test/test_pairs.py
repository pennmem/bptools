import os.path as osp
import json
import pytest

import numpy as np
import pandas as pd

from bptools.pairs import create_pairs, pairs_to_json, write_pairs
from bptools.test import datafile, tempdir


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


def test_pairs_to_json():
    pairs = create_pairs(datafile('R1308T_jacksheet.txt'))

    with tempdir() as path:
        pairs_to_json(pairs, 'R1308T', path)
        pair_list = pairs.pair.tolist()
        outfile = osp.join(path, 'pairs.json')
        assert osp.exists(outfile)

        with open(outfile, 'r') as f:
            result = json.loads(f.read())
            assert 'R1308T' in result.keys()
            assert 'pairs' in result['R1308T'].keys()
            for key in result['R1308T']['pairs']:
                assert key in pair_list


def test_write_pairs():
    pairs = create_pairs(datafile('R1308T_jacksheet.txt'))

    # Unsupported file type
    with tempdir() as path:
        filename = osp.join(path, "test.xyz")
        with pytest.raises(ValueError):
            write_pairs(pairs, filename)

    # CSV files
    with tempdir() as path:
        filename = osp.join(path, 'test.csv')
        write_pairs(pairs, filename)

        df = pd.read_csv(filename)
        for column in pairs.columns:
            assert all(df[column] == pairs[column])

    # JSON files
    with tempdir() as path:
        filename = osp.join(path, 'pairs.json')

        # No subject
        with pytest.raises(ValueError):
            write_pairs(pairs, filename)

        write_pairs(pairs, filename, subject='R0000X')

        with open(filename, 'r') as f:
            data = json.loads(f.read())
            assert 'R0000X' in data
            # Not testing remainder since covered in test_pairs_to_json
