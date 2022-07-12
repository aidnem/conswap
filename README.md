# confman
A config manager/swapper written in python

Confman is under development so it may be buggy and things may change.

## Installation
To install, simply clone the repo.

## Usage
To run confman, run `confman.py` with python 3.10.

Options:

* `--help` (`-h`) - Print help message and quit

* `--debug` (`-d`) - Print debug messages


The first time confman is run, it will create the folders `~/.config/confman/` and `~/.config/confman/groups/`
Any confman related files will be kept in `~/.config/confman`.
Groups will be kept in `~/.config/confman/groups/`.

### Commands
Confman needs to be run with a command to actually do anything.

The currently implemented commands are:

* `new` - Create a new group

  Options:
    * `--dest` (`-d`) - Change the destination path, where the files will be swapped to.

  **Note: options for subcommands must be placed *after* the subcommand itself.**

