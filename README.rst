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

Script usage::

    usage: python -m bptools.odin [-h] [--jacksheet JACKSHEET] --subject SUBJECT
                                  [--localization LOCALIZATION]
                                  [--montage MONTAGE] [--stim]
                                  [--surface-area SURFACE_AREA]
                                  [--output-path OUTPUT_PATH]
                                  [--rhino-root RHINO_ROOT]

    Odin config generator

    optional arguments:
      -h, --help            show this help message and exit
      --jacksheet JACKSHEET, -j JACKSHEET
                            path to jacksheet file
      --subject SUBJECT, -s SUBJECT
                            subject ID
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

    DON'T PANIC

If no jacksheet is specified, the script will try to automatically find it based
on the subject ID.

Stimulation channels must be defined manually via the Odin configuration tool
GUI.

.. warning::

    In order to properly handle micro contacts on combined macro/micro
    electrodes, labels in the jacksheet **must** be different for the macro and
    micro contacts.
