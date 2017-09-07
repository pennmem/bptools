import os.path as osp

from .jacksheet import read_jacksheet
from .pairs import create_pairs


def _num_to_bank_label(num):
    """Convert a channel number to a more human-friendly ENS bank label (e.g.,
    1 -> A-CH01).

    """
    banks = {
        0: 'A',
        1: 'B',
        2: 'C',
        3: 'D'
    }
    bank = banks[num // 64]
    return "{}-CH{:02d}".format(bank, num % 64)


def make_odin_config(filename, name, subject, path=None):
    """Create an Odin ENS electrode configuration CSV file.

    Parameters
    ----------
    filename : str
        Input filename.
    name : str
        Configuration file name.
    subject : str
        Subject ID.
    path : str
        Directory to write file to. If None, return as a string.

    """
    js = read_jacksheet(filename)
    pairs = create_pairs(filename)

    # Header
    config = [
        "ODINConfigurationVersion:,# 1.2#",
        "ConfigurationName:," + name,
        "SubjectID:," + subject,
        "Contacts:",
    ]

    # Channel definitions
    for n, row in js.iterrows():
        jbox_num = n
        chan = _num_to_bank_label(jbox_num)
        data = [row.label, str(jbox_num), str(jbox_num), "0.001",
                "#Electrode {} jack box {}#".format(chan, jbox_num)]
        config.append(','.join(data))

    # Sense definitions
    config.append("SenseChannelSubclasses")
    config.append("SenseChannels:")
    for _, row in pairs.iterrows():
        data = [row.label1, row.pair.replace('-', ''),
                str(row.contact1), str(row.contact2), 'x',
                "#{}#".format(row.pair)]
        config.append(','.join(data))

    # Stim definitions
    # TODO
    config.append("StimulationChannelSubclasses:")
    config.append("StimulationChannels:")
    config.append("REF:,0,Common")
    config.append('EOF')

    if path is not None:
        outfile = osp.join(path, '{}_{}.csv'.format(subject, name))
        with open(outfile, 'w') as f:
            outfile.writelines(config)
    else:
        return "\n".join(config)
