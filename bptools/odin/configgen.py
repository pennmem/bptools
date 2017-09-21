import os.path as osp
from datetime import datetime

from bptools.jacksheet import read_jacksheet
from bptools.pairs import create_pairs, create_monopolar_pairs


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


def make_odin_config(jacksheet_filename, config_name, default_surface_area,
                     path=None, good_leads=None, scheme='bipolar'):
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
    scheme : str
        Referencing scheme to use (``bipolar`` or ``monopolar``).

    Notes
    -----
    In the future, jacksheets should optionally include extra annotations such
    as type of electrode (depth, grid, strip) and surface areas.

    """
    assert isinstance(default_surface_area, float)
    assert scheme in ['bipolar', 'monopolar'], "invalid referencing scheme"

    js = read_jacksheet(jacksheet_filename)

    if scheme == 'bipolar':
        pairs = create_pairs(jacksheet_filename)
    elif scheme == 'monopolar':
        pairs = create_monopolar_pairs(jacksheet_filename)

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
            if row.contact1 not in good_leads:
                continue
            if row.contact2 not in good_leads and scheme != "monopolar":
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

