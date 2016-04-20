fflipper
================================

A video clipper that takes ELAN files as it's input, and generates clips based on the annotations in a selected tier.


## Installation

To install on OS X (tested and works with Yosemite:)

### Install [Homebrew](http://brew.sh/) with the command 

`ruby -e "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/master/install)"`

If this doesn't work, consult the Homebrew documentation.

### Install python and tk from brew
`brew install python --with-tcl-tk`

### Install ElementTree for python:
`easy_install elementtree` should work, if not try `sudo easy_install elementtree`

### Download fflipper, [pyelan](https://github.com/jonkeane/pyelan), and [clipper](https://github.com/jonkeane/clipper).
Move these into the fflipper folder, and make sure that each folder is named just `pyelan` and `clipper` respectively (ie remove the `-master`, if you downloaded them from GitHub as archives.)

### Run
Use the command `python /path/to/fflipper/fflipper.py` in the terminal to run ffliper, remember to change the /path/to part to the location of fflipper on your machine.

Some development of this project was supported by a grant from the national sicence foundation: NFS BCS 1251807



TODO
-------------------------
* subprocess polling
* rewrite clipper
* progress bars
* package for distribution

