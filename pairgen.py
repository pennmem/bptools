"""Test script for pair generation."""

import pandas as pd


with pd.option_context('display.max_rows', None, 'display.max_columns', None):
    from bptools import create_pairs
    pairs = create_pairs("bptools/test/data/R1308T_jacksheet.txt")
    print('\n', pairs)
