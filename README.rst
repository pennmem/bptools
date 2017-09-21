bptools
=======

.. image:: https://travis-ci.org/pennmem/bptools.svg?branch=master
    :target: https://travis-ci.org/pennmem/bptools

.. image:: https://codecov.io/gh/pennmem/bptools/branch/master/graph/badge.svg
  :target: https://codecov.io/gh/pennmem/bptools

EEG bipolar montage helpers.

`Documentation <https://pennmem.github.io/bptools/html/index.html>`_


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


Known issues
^^^^^^^^^^^^

There is a bug in the Odin configuration tool which will silently accept the
same primary contact in multiple sense channels. For example, it would indicate
passing all checks if there were pairs defined as ``LA1-LA2`` and ``LA1-LA9``.
This is handled automatically in the CSV generation script by flipping the order
of contacts in the case of distal pairings. In other words, the pairs above will
instead be defined as ``LA1-LA2`` and ``LA9-LA1``.
