Changes
=======

Version 1.3.1
-------------

**2022-12-07**

* Added python 3.7 support


Version 1.3.0
-------------

**2018-01-17**

* Updated ``ElectrodeConfig.contacts`` to be an ``OrderedDict`` instead of a
  list (#17). This fixes an issue with broken config file generation when a
  jacksheet contains ignored contacts (e.g., ``EKG``) in between non-ignored
  contacts.
* Disabled label standardization by default
* Enabled some testing of the ``bptools.transform`` module


Version 1.2.3
-------------

**2017-12-18**

* Bugfix release to add a newline character after ``EOF`` in the binary config
  file.

Version 1.2.2
-------------

**2017-12-15**

* Added simple validation for surface area files.
* Fixed bug where surface areas could be pandas ``Series`` objects rather than
  floats.


Version 1.2.1
-------------

**2017-12-13**

* Automated setting surface areas by reading from a file
* Taught ``ElectrodeConfig`` objects how to output to CSV and binary files


Version 1.2.0
-------------

**2017-12-12**

* Added ability to generate Odin binary configuration files in addition to CSV
  files


Version 1.1.2
-------------

**2017-10-23**

* Stopped standardizing labels by default (this could sometimes cause issues
  and was never strictly necessary)


Version 1.1.1
-------------

**2017-10-11**

* Added a method for standardizing labels and defaulted to using these
* Aliased "name" with "label"
* Added a utility to find existing Odin electrode configuration files


Version 1.1.0
-------------

**2017-09-29**

* Added support for "monopolar" (common reference) electrode configuration
* Added auto-generated documentation
* Numerous bug fixes and workflow improvements


Version 1.0.0
-------------

**2017-09-12**

Initial release supporting creation of true bipolar electrode configuration
files for the Odin ENS.
