Changes
=======

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
