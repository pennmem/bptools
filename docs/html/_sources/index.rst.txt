bptools
=======

EEG bipolar montage helpers.


Electrode config generation
---------------------------

Electrode configuration CSV files can be generated for the Medtronic Odin ENS
using the CLI tool provided in :mod:`bptools.odin`::

    usage: python -m bptools.odin [-h] [--scheme {bipolar,monopolar}]
                                  [--jacksheet JACKSHEET]
                                  [--good-leads GOOD_LEADS]
                                  [--localization LOCALIZATION]
                                  [--montage MONTAGE] [--stim]
                                  [--surface-area SURFACE_AREA]
                                  [--output-path OUTPUT_PATH]
                                  [--rhino-root RHINO_ROOT] --subject SUBJECT

    Odin config generator

    optional arguments:
      -h, --help            show this help message and exit
      --scheme {bipolar,monopolar}
                            configuration scheme to use (default: bipolar)
      --jacksheet JACKSHEET, -j JACKSHEET
                            path to jacksheet file
      --good-leads GOOD_LEADS, -g GOOD_LEADS
                            path to good_leads.txt
      --localization LOCALIZATION, -l LOCALIZATION
                            localization number (default: 0)
      --montage MONTAGE, -m MONTAGE
                            montage number (default: 0)
      --stim, -S            flag to enable stim (default: False)
      --surface-area SURFACE_AREA, -a SURFACE_AREA
                            default surface area in mm^2 (default: 0.001)
      --output-path OUTPUT_PATH, -o OUTPUT_PATH
                            directory to write output to
      --rhino-root RHINO_ROOT, -r RHINO_ROOT
                            rhino root path for jacksheet discovery (default: "/")
      --subject SUBJECT, -s SUBJECT
                            subject ID

If no jacksheet is specified, the script will try to automatically find it based
on the subject ID.

The general workflow is as follows:

1. Generate CSV config file with the script provided here.
2. Edit the CSV config file to include the proper surface areas for each contact.
3. Load the CSV config in the Odin configuration tool.
4. Define stim channels if applicable.
5. Save the CSV config file.
6. Save the binary config file.

To run the script, either run from the root directory of ``bptools``, add said
directory to your ``PYTHONPATH``, or run ``python setup.py install`` so that it
is always reachable from your environment.

.. note::

    Stimulation channels must be defined manually via the Odin configuration
    tool GUI.

.. warning::

    In order to properly handle micro contacts on combined macro/micro
    electrodes, labels in the jacksheet **must** be different for the macro and
    micro contacts when using bipolar referencing.

Known issues
^^^^^^^^^^^^

There is a bug in the Odin configuration tool which will silently accept the
same primary contact in multiple sense channels. For example, it would indicate
passing all checks if there were pairs defined as ``LA1-LA2`` and ``LA1-LA9``.
This is handled automatically in the CSV generation script by flipping the order
of contacts in the case of distal pairings. In other words, the pairs above will
instead be defined as ``LA1-LA2`` and ``LA9-LA1``.


API reference
-------------

Jacksheet utilities
^^^^^^^^^^^^^^^^^^^

.. automodule:: bptools.jacksheet
    :members:

Pair creation tools
^^^^^^^^^^^^^^^^^^^

.. automodule:: bptools.pairs
    :members:

Odin ENS configuration
^^^^^^^^^^^^^^^^^^^^^^

.. automodule:: bptools.odin
    :members:

.. .. toctree::
   :maxdepth: 2
   :caption: Contents:
