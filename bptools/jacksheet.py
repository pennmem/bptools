import pandas as pd


def read_jacksheet(filename):
    """Utility function to read a jacksheet.

    Parameters
    ----------
    filename : str

    Returns
    -------
    pd.DataFrame

    """
    df = pd.read_csv(filename, index_col=0, names=['label'], sep='\s+')
    electrodes = df.label.str.extract(r'(^[a-zA-Z]+)', expand=True) \
        .rename(columns={0: 'electrode'})
    return pd.concat([df, electrodes], axis=1)
