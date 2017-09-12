from __future__ import print_function

import os.path as osp
from argparse import ArgumentParser
from datetime import datetime

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


def _read_good_leads(filename):
    with open(filename, 'r') as f:
        good_leads = [int(c) for c in f.read().split()]
    return good_leads


def make_odin_config(jacksheet_filename, config_name, default_surface_area,
                     path=None, good_leads=None):
    """Create an Odin ENS electrode configuration CSV file.

    Parameters
    ----------
    jacksheet_filename : str
        Input jacksheet filename.
    config_name : str
        Configuration file name.
    default_surface_area : float
        Default surface area for electrodes.
    path : str
        Directory to write file to. If None, return as a string.
    good_leads : list or None
        Jackbox numbers to use when configuring sense channels. This is usually
        determined from the ``good_leads.txt`` file. When None, use all.

    Notes
    -----
    In the future, jacksheets should optionally include extra annotations such
    as type of electrode (depth, grid, strip) and surface areas.

    """
    assert isinstance(default_surface_area, float)

    js = read_jacksheet(jacksheet_filename)
    pairs = create_pairs(jacksheet_filename)

    subject, name = config_name.split('_')

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
        data = [row.label, str(jbox_num), str(jbox_num), "{:.03f}".format(default_surface_area),
                "#Electrode {} jack box {}#".format(chan, jbox_num)]
        config.append(','.join(data))

    # Sense definitions
    config.append("SenseChannelSubclasses:")
    config.append("SenseChannels:")
    for _, row in pairs.iterrows():
        if good_leads is not None:
            if row.contact1 not in good_leads or row.contact2 not in good_leads:
                continue
        data = [row.label1, row.pair.replace('-', ''),
                str(row.contact1), str(row.contact2), 'x',
                "#{}#".format(row.pair)]
        config.append(','.join(data))

    # Stim definitions
    config.append("StimulationChannelSubclasses:")
    config.append("StimulationChannels:")
    config.append("REF:,0,Common")
    config.append('EOF')

    if path is not None:
        outfile = osp.join(path, config_name + '.csv')
        with open(outfile, 'w') as f:
            f.write('\n'.join(config))
            f.write('\n')
    else:
        return "\n".join(config)


def make_config_name(subject, localization, montage, stim):
    """Create the configuration filename using the standard naming convetion.

    Parameters
    ----------
    subject : str
    localization : int
    montage : int
    stim : bool

    """
    now = datetime.now()
    name_tmpl = "{subject:s}_{day:02d}{month:s}{year:04d}L{localization:d}M{montage:d}{stim:s}"
    name = name_tmpl.format(**{
        'subject': subject,
        'day': now.day,
        'month': now.strftime('%b'),
        'year': now.year,
        'localization': localization,
        'montage': montage,
        'stim': 'STIM' if stim else 'NOSTIM'
    })
    return name.upper()


def main():  # pragma: nocover
    """Command-line interface for generating Odin config files."""
    parser = ArgumentParser(prog='python -m bptools.odin',
                            description="Odin config generator",
                            epilog="DON'T PANIC")
    parser.add_argument("--jacksheet", "-j", type=str, help='path to jacksheet file')
    parser.add_argument("--good-leads", "-g", type=str, help="path to good_leads.txt")
    parser.add_argument("--localization", "-l", default=0, type=int,
                        help='localization number (default: 0)')
    parser.add_argument("--montage", "-m", default=0, type=int,
                        help='montage number (default: 0)')
    parser.add_argument("--stim", "-S", action='store_true', default=False,
                        help='flag to enable stim (default: False)')
    parser.add_argument("--surface-area", "-a", default=0.001, type=float,
                        help="default surface area in mm^2")
    parser.add_argument("--output-path", "-o", type=str, help='directory to write output to')
    parser.add_argument("--rhino-root", "-r", type=str, default="/",
                        help='rhino root path for jacksheet discovery (default: "/")')
    parser.add_argument("--subject", "-s", type=str, required=True, help='subject ID')
    args = parser.parse_args()

    root = args.rhino_root if args.rhino_root.endswith("/") else args.rhino_root + "/"
    root = osp.expanduser(root)
    if args.jacksheet is None:
        jacksheet = osp.join(root, "data", "eeg", args.subject, "docs", "jacksheet.txt")
    else:
        jacksheet = args.jacksheet

    if args.good_leads is None:
        good_leads_file = osp.join(root, "data", "eeg", args.subject, "tal", "good_leads.txt")
        if not osp.exists(good_leads_file):
            print("Warning: no good_leads.txt found! Assuming all contacts are good...")
            good_leads = None
        else:
            good_leads = _read_good_leads(good_leads_file)
    else:
        good_leads = _read_good_leads(args.good_leads)

    name = make_config_name(args.subject, args.localization, args.montage, args.stim)
    res = make_odin_config(jacksheet, name, args.surface_area, args.output_path,
                           good_leads=good_leads)
    if res is not None:
        print(res)
    else:
        print("Wrote", osp.join(args.output_path, name + ".csv"))


if __name__ == "__main__":  # pragma: nocover
    main()
