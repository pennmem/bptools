bptools
=======

.. image:: https://travis-ci.org/pennmem/bptools.svg?branch=master
    :target: https://travis-ci.org/pennmem/bptools

.. image:: https://codecov.io/gh/pennmem/bptools/branch/master/graph/badge.svg
  :target: https://codecov.io/gh/pennmem/bptools

EEG bipolar montage helpers.


Odin ENS electrode configuration
--------------------------------

General workflow:

1. Generate CSV config file with the script provided here.
2. Edit the CSV config file to include the proper surface areas for each contact.
3. Load the CSV config in the Odin configuration tool.
4. Define stim channels if applicable.
5. Save the CSV config file.
6. Save the binary config file.

To run the script, either run from the same directory as this README, add said
directory to your ``PYTHONPATH``, or run ``python setup.py install``.

Script usage::

    usage: python -m bptools.odin [-h] [--jacksheet JACKSHEET]
                                  [--good-leads GOOD_LEADS]
                                  [--localization LOCALIZATION]
                                  [--montage MONTAGE] [--stim]
                                  [--surface-area SURFACE_AREA]
                                  [--output-path OUTPUT_PATH]
                                  [--rhino-root RHINO_ROOT] --subject SUBJECT

    Odin config generator

    optional arguments:
      -h, --help            show this help message and exit
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
                            default surface area in mm^2
      --output-path OUTPUT_PATH, -o OUTPUT_PATH
                            directory to write output to
      --rhino-root RHINO_ROOT, -r RHINO_ROOT
                            rhino root path for jacksheet discovery (default: "/")
      --subject SUBJECT, -s SUBJECT
                            subject ID

    DON'T PANIC

If no jacksheet is specified, the script will try to automatically find it based
on the subject ID.

Stimulation channels must be defined manually via the Odin configuration tool
GUI.

.. warning::

    In order to properly handle micro contacts on combined macro/micro
    electrodes, labels in the jacksheet **must** be different for the macro and
    micro contacts.

Known issues
^^^^^^^^^^^^

There is a bug in the Odin configuration tool which will silently accept the
same primary contact in multiple sense channels. For example, it would indicate
passing all checks if there were pairs defined as ``LA1-LA2`` and ``LA1-LA9``.
This is handled automatically in the CSV generation script by flipping the order
of contacts in the case of distal pairings. In other words, the pairs above will
instead be defined as ``LA1-LA2`` and ``LA9-LA1``.
