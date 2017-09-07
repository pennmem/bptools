import os.path as osp
from argparse import ArgumentParser

from bptools.jacksheet import read_jacksheet
from bptools.pairs import create_pairs


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
        "ODINConfigurationVersion:,#1.2#",
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
    config.append("SenseChannelSubclasses:")
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
            f.write('\n'.join(config))
            f.write('\n')
    else:
        return "\n".join(config)


def main():
    """Command-line interface for generating Odin config files."""
    parser = ArgumentParser(description="Odin config generator")
    parser.add_argument("--jacksheet", "-j", type=str, help='path to jacksheet file')
    parser.add_argument("--name", "-n", type=str, required=True, help='configuration name')
    parser.add_argument("--subject", "-s", type=str, required=True, help='subject ID')
    parser.add_argument("--output-path", "-o", type=str, help='path to write output to')
    parser.add_argument("--rhino-root", "-r", type=str, default="/", help="rhino root path for jacksheet discovery")
    args = parser.parse_args()

    if args.jacksheet is None:
        root = args.rhino_root if args.rhino_root.endswith("/") else args.rhino_root + "/"
        jacksheet = osp.expanduser(root) + osp.join("data", "eeg", args.subject, "docs", "jacksheet.txt")
    else:
        jacksheet = args.jacksheet

    res = make_odin_config(jacksheet, args.name, args.subject, args.output_path)
    if res is not None:
        print(res)


if __name__ == "__main__":
    main()
