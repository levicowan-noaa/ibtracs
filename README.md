# Python IBTrACS API

A Python interface to the IBTrACS tropical cyclone best track dataset.

## Dependencies
- Numpy >= 1.7
- Python >= 3.6

## Installation

```
git clone https:/www.github.com/levicowan/ibtracs
cd ibtracs
./install.sh
```

This will download the IBTrACS v4r00 CSV file from NCEI (URL will need updating when new versions get released), set up the ibtracs directory created above, and add its parent directory to $PYTHONPATH so that the module is importable.

## Usage

Initial setup:
```
from ibtracs import Ibtracs
I = Ibtracs()
