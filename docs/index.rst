bptools
=======

EEG bipolar montage helpers.


Electrode config generation
---------------------------

.. warning::

    The CLI described below is considered deprecated as of 2017-12-13. The recommended
    way of generating electrode configuration files is via the ``ramutils``
    package which uses the :mod:`bptools` API internally. This user interface
    may be removed entirely in future releases in favor of using the API only.

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

Both CSV and binary config files will be generated. This command-line tool has
no way of specifying surface areas (other than a common default surface area) or
of defining stim channels. It exists primarily for historical reasons and for
rapid testing.

To run the script, either run from the root directory of ``bptools``, add said
directory to your ``PYTHONPATH``, or run ``python setup.py install`` so that it
is always reachable from your environment.

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

The general workflow for creating electrode configuration files:

* Create a :class:`bptools.odin.ElectrodeConfig` object using its
  :func:`from_jacksheet` method: ``ec = ElectrodeConfig.from_jacksheet(path_to_jacksheet_file)``
* Populate stim channels: ``ec.add_stim_channel('LA1', 'LA2')``
* Save as CSV: ``ec.to_csv(path_to_csv_file)``
* Save as binary: ``ec.to_bin(path_to_csv_file``

.. automodule:: bptools.odin.config
    :members:

Bipolar transformation utilities
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. autoclass:: bptools.transform.SeriesTransformation
    :members:

.. .. toctree::
   :maxdepth: 2
   :caption: Contents:
