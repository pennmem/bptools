from __future__ import print_function

from argparse import ArgumentParser
import os.path as osp

from .config import make_config_name, make_odin_config


def _read_good_leads(filename):
    with open(filename, 'r') as f:
        good_leads = [int(c) for c in f.read().split()]
    return good_leads


def main(args=None):
    """Command-line interface for generating Odin config files."""
    parser = ArgumentParser(prog='python -m bptools.odin',
                            description="Odin config generator",
                            epilog="DON'T PANIC")
    parser.add_argument("--scheme", choices=["bipolar", "monopolar"],
                        default="bipolar",
                        help="configuration scheme to use (default: bipolar)")
    parser.add_argument("--jacksheet", "-j", type=str, help='path to jacksheet file')
    parser.add_argument("--good-leads", "-g", type=str, help="path to good_leads.txt")
    parser.add_argument("--localization", "-l", default=0, type=int,
                        help='localization number (default: 0)')
    parser.add_argument("--montage", "-m", default=0, type=int,
                        help='montage number (default: 0)')
    parser.add_argument("--stim", "-S", action='store_true', default=False,
                        help='flag to enable stim (default: False)')
    parser.add_argument("--surface-area", "-a", default=0.001, type=float,
                        help="default surface area in mm^2 (default: 0.001)")
    parser.add_argument("--output-path", "-o", type=str, help='directory to write output to')
    parser.add_argument("--rhino-root", "-r", type=str, default="/",
                        help='rhino root path for jacksheet discovery (default: "/")')
    parser.add_argument("--subject", "-s", type=str, required=True, help='subject ID')
    args = parser.parse_args(args)

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
                           good_leads=good_leads, scheme=args.scheme)
    if res is not None:
        print(res)
    else:
        print("Wrote", osp.join(args.output_path, name + ".csv"))
