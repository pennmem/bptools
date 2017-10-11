"""Utilities to fetch existing electrode config files from uploaded RAM data.

"""

from os.path import expanduser
from pathlib import Path


def get_odin_config_path(subject, experiment, root='/'):
    """Return the full path to an Odin config file for a given experiment. This
    function will return only the first config file it finds, so if the
    configuration changed between sessions, the resulting path should be
    updated accordingly by hand.

    Parameters
    ----------
    subject : str
    experiment : str
    root : str
        Rhino root path

    Returns
    -------
    bin : str
        Path to binary config file

    """
    subj_dir = Path(expanduser(root)) / 'data' / 'eeg' / subject / 'behavioral'
    exp_dir = subj_dir / experiment
    bin = list(exp_dir.rglob('*.bin'))[0]
    return str(bin)


if __name__ == "__main__":
    out = get_odin_config_path('R1351M', 'FR5', '~/mnt/rhino')
    print(out)
