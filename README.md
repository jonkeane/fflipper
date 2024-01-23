fflipper
================================

A video clipper that takes ELAN files as it's input and generates clips based on the annotations in a selected tier.


## Installation

fflipper installs as a standard macOS application. There are two different versions for macs with apple M-based chips (e.g. M1, M2, M3) and older macs with x86 processors.

#### [Download for M-based macs](https://github.com/jonkeane/fflipper/releases/download/0.1.0-rc/fflipper.pkg)

#### [Download for x86 macs](https://github.com/jonkeane/fflipper/releases/download/0.1.0-rc/fflipper_x86.pkg) (only needed for older macs)

If you try one and get an error, try the other.

## Developer installation

fflipper uses the [poetry](https://python-poetry.org) for installation and dependency management. One you [install poetry](https://python-poetry.org/docs/#installation), you should be able to do the following (all from inside of the fflipper directory):

```
poetry install
poetry shell
python run_app.py
```

## Harder installation

Only use this method if you are having issues installing using the section above. This might not work depending on your system.

* Backup, alternative for M-based macs: `https://github.com/jonkeane/fflipper/releases/download/0.1.0-rc/fflipper_backup_alternative`
* Backup, alternative for x86 macs: `https://github.com/jonkeane/fflipper/releases/download/0.1.0-rc/fflipper_x86_backup_alternative` (only needed for older macs)
