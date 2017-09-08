bptools
=======

.. image:: https://travis-ci.org/pennmem/bptools.svg?branch=master
    :target: https://travis-ci.org/pennmem/bptools

.. image:: https://codecov.io/gh/pennmem/bptools/branch/master/graph/badge.svg
  :target: https://codecov.io/gh/pennmem/bptools

EEG bipolar montage helpers.


Odin ENS electrode configuration
--------------------------------

Usage::

    $ python -m bptools.odin -h
    usage: odin.py [-h] [--jacksheet JACKSHEET] --name NAME --subject SUBJECT
                   [--output-path OUTPUT_PATH] [--rhino-root RHINO_ROOT]

    Odin config generator

    optional arguments:
      -h, --help            show this help message and exit
      --jacksheet JACKSHEET, -j JACKSHEET
                            path to jacksheet file
      --name NAME, -n NAME  configuration name
      --subject SUBJECT, -s SUBJECT
                            subject ID
      --output-path OUTPUT_PATH, -o OUTPUT_PATH
                            directory to write output to
      --rhino-root RHINO_ROOT, -r RHINO_ROOT
                            rhino root path for jacksheet discovery (default: "/")

If no jacksheet is specified, the script will try to automatically find it based
on the subject ID.

Stimulation channels must be defined manually via the Odin configuration tool
GUI.

.. warning::

    In order to properly handle micro contacts on combined macro/micro
    electrodes, labels in the jacksheet **must** be different for the macro and
    micro contacts.
