# conswap
A config manager/swapper written in python

> conswap used to be named confman, but was renamed due to the existence of
other projects under the same name.

conswap is under development so it may be buggy and things may change.

## Installation
To install, simply clone the repo.

## Usage
To run conswap, run `conswap.py` with python 3.10.

Options:

* `--help` (`-h`) - Print help message and quit

> The `-h` option exists for every subcommand as well.

* `--debug` (`-d`) - Print debug messages


The first time conswap is run, it will create the folders `~/.config/conswap/` and `~/.config/conswap/groups/`
Any conswap related files will be kept in `~/.config/conswap`.
Groups will be kept in `~/.config/conswap/groups/`.

### Commands
conswap needs to be run with a command to actually do anything.

The currently implemented commands are:

* `new` - Create a new group

  Usage: `<conswap> new <name>`

  Arguments:
    * `<name>` - the name of the group

  Options:
    * `--dest` (`-dt`) - Change the destination path, where the files will be swapped to.
    * `--desc` (`-dc`) - Change the group description, which will show up in the `list` command.

  **Note: options for subcommands must be placed *after* the subcommand itself.**

* `delete` - Remove a group

  Usage: `<conswap> delete <name>`

  Arguments:
    * `<name>` - the name of the group being deleted

* `list` - List existing groups or configs in a group

  Usage `<conswap> list`

  Arguments:
    * `--group` (`-g`) - name of group to list configs for (if `-g` is not present, `list` will list all configs)

* `fix` - Fix broken 'group.toml'files

  Usage `<conswap> fix`

  Arguments:
    * `--verbose` (`-v`) - Print detailed messages for each fix made.

* `configure` - Configure a group (set fields in a specific group's 'group.toml' file)

  Usage: `<conswap> configure <group>`

  Arguments:
    * `<name>` - Name of the group to configure

* `swap` - Swap between configs for a specific group

  Usage: `<conswap> swap <group> <config>`

  Arguments:
    * `<group>` - Which group to swap configs for
    * `<config>` - Which config to swap to

