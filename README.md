# confman
A config manager/swapper written in python

Confman is under development so it may be buggy and things may change.

## Installation
To install, simply clone the repo.

## Usage
To run confman, run `confman.py` with python 3.10.

Options:

* `--help` (`-h`) - Print help message and quit

> The `-h` option exists for every subcommand as well.

* `--debug` (`-d`) - Print debug messages


The first time confman is run, it will create the folders `~/.config/confman/` and `~/.config/confman/groups/`
Any confman related files will be kept in `~/.config/confman`.
Groups will be kept in `~/.config/confman/groups/`.

### Commands
Confman needs to be run with a command to actually do anything.

The currently implemented commands are:

* `new` - Create a new group

  Usage: `<confman> new <name>`

  Arguments:
    * `<name>` - the name of the group

  Options:
    * `--dest` (`-dt`) - Change the destination path, where the files will be swapped to.
    * `--desc` (`-dc`) - Change the group description, which will show up in the `list` command.

  **Note: options for subcommands must be placed *after* the subcommand itself.**

* `delete` - Remove a group

  Usage: `<confman> delete <name>`

  Arguments:
    * `<name>` - the name of the group being deleted

* `list` - List existing groups

  Usage `<confman> list`

  Arguments:
    * `--verbose` (`-v`) - Display swap destination for each group in addition to other info.

* `fix` - Fix broken 'group.toml'files

  Usage `<confman> fix`

  Arguments:
    * `--verbose` (`-v`) - Print detailed messages for each fix made.

* `configure` - Configure a group (set fields in a specific group's 'group.toml' file)

  Usage: `<confman> configure <group>`

  Arguments:
    * `<name>` - Name of the group to configure

* `swap` - Swap between configs for a specific group

  Usage: `<confman> swap <group> <config>`

  Arguments:
    * `<group>` - Which group to swap configs for
    * `<config>` - Which config to swap to

