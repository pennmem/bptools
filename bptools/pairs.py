import pandas as pd


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
    df = pd.read_csv(jacksheet_filename, index_col=0, names=['label'], sep='\s+')
    electrodes = df.label.str.extract(r'(^[a-zA-Z]+)', expand=True)\
        .rename(columns={0: 'electrode'})
    jacksheet = pd.concat([df, electrodes], axis=1)
    groups = jacksheet.electrode.unique()

    pairs = []
    mux = 0

    for group in groups:
        mux_crossed = -1

        el = jacksheet[jacksheet.electrode == group]
        for i in range(len(el) - 1):
            mux += 1

            # MUX crossing
            if mux % 32 == 0 and mux != 0 and i != 0:
                mux_crossed = i
                pairs.append("{}-{}".format(el.iloc[i].label, el.iloc[0].label))
                continue

            # Last contact
            elif i == len(el) - 1:
                b = el.iloc[-1].label
                if mux_crossed < 0:
                    a = el.iloc[0].label
                else:
                    a = el.iloc[mux_crossed].label

                if a != b:
                    pairs.append("{}-{}".format(a, b))

            # Adjacent contacts
            # FIXME: handle MUX crossing
            else:
                pairs.append("{}-{}".format(el.iloc[i].label, el.iloc[i + 1].label))

    pdf = pd.DataFrame(dict(pair=pairs))
    return pdf


if __name__ == "__main__":
    from pathlib import Path
    filename = Path("~/mnt/rhino/data/eeg/R1308T/docs/jacksheet.txt")
    pairs = create_pairs(filename.expanduser().absolute())

    for n, row in pairs.iterrows():
        print(n + 1, row.pair)
