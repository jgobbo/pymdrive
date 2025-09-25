# PyMDrive

PyMDrive is a python driver for MDrive motors. It has wrappers for standard commands (home, move absolute, move relative, etc.) and any other MCode command can be added easily.

## Installation

It is easiest to install with pip: `pip install pymdrive`

You can also install with [uv](https://docs.astral.sh/uv/) by cloning the repo and using `uv sync`.

## Usage

To get started do

```python
from pymdrive import MdriveAxis, MdriveComm

COMM = MdriveComm("COM3")
await COMM.start()

X = MdriveAxis(comm=COMM, name="X")
Y = MdriveAxis(comm=COMM, name="Y")
```

This initializes the COMM and starts its asynchronous queue for processing commands without race conditions. The COMM is then passed to Axis instances where the names are those specified on the motors memory.

From there, you can send standard commands

```python
await X.move_relative(1000)

await Y.move_absolute(0)
```

There's a `testing.ipynb` notebook in the `tests` directory with these and other commands.