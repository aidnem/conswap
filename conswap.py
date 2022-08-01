"""Manage and swap configuration files

This module isn't intended to be imported, it is a CLI tool."""

import logging
from argparse import ArgumentParser
import os
import pathlib
import sys
from typing import Callable, Literal
import toml
import shutil
import subprocess


CONFIG_PATH_SUFFIX = ".config/conswap"
GROUPS_SUFFIX = "groups"
CONFIG_PATH = os.path.join(pathlib.Path.home(), CONFIG_PATH_SUFFIX)
GROUPS_PATH = os.path.join(CONFIG_PATH, GROUPS_SUFFIX)
NOT_CONFIGURED = "NOT CONFIGURED"
GROUP_CFG_FN = "group.toml"
GROUP_CFG_DATA = {
    "desc"     : "", # Group description
    "dest_path": NOT_CONFIGURED, # Group swap destination
}

def ensure_config_dir():
    """Ensure that the config directory exists, and if not creates it"""
    if os.path.isdir(GROUPS_PATH):
        logging.debug(f"Found {GROUPS_PATH}")
    else:
        print(f"No groups directory was found, creating it in {GROUPS_PATH}")

        os.makedirs(GROUPS_PATH)

        if os.path.isdir(GROUPS_PATH):
            logging.debug("Created config and groups directories")
        else:
            logging.critical(f"Failed to create config folder; exitting")
            sys.exit()


def confirm(prompt: str) -> bool:
    """Prompt a user to confirm"""
    return input(f"{prompt}\n[y/N]").lower() == "y"


def confirm_call(func: Callable, *args, auto_exit=True):
    """Call a function with given arguments after making user confirm"""
    if confirm(
        f"OK to call function '{func.__name__}' with args {args}? This might delete or destroy the file/folder."
    ):
        func(*args)
        return True

    if auto_exit:
        logging.critical("Function call aborted, exitting")
        sys.exit()
    else:
        print("Function call cancelled")
        sys.exit()


def validate_name(name, auto_exit=True):
    """Ensure that a name is valid (letters, numbers, and _ only)"""
    for c in name:
        if not (c.isalnum() or c == "_"):
            logging.critical(
                f"Character {c} is not allowed in group name (must be letters, numbers, or '_')"
            )
            if auto_exit:
                sys.exit(1)
            else:
                return False

    return True


def expand_path(path: str) -> str:
    """Fully expand a path, including expanding relative paths, paths starting with '~', and $VARIABLES"""
    return os.path.abspath(os.path.expanduser(os.path.expandvars(path)))


def expand_path_safe(path: str) -> str:
    """Fully expand a path, including expanding relative paths, paths starting with '~', and $VARIABLES, and ensure that is under the user's home directory"""
    path = expand_path(path)
    # Make sure user doesn't accidentally delete /bin or something crazy like that
    if not path.startswith(str(pathlib.Path.home())):
        logging.critical("For security reasons, paths outside of your home directory are not allowed")
        sys.exit(1)

    return path


def get_group_path(name: str) -> str:
    """Get the path to a group given the name of the group"""
    validate_name(name)
    group_path = os.path.join(GROUPS_PATH, name)
    print(group_path)
    return expand_path_safe(group_path)


def command_new(name: str, dest_path: str, group_desc: str):
    """Creates a new group given the name"""
    dest_path = expand_path_safe(dest_path)

    validate_name(name)
    group_path = get_group_path(name)
    group_cfg_path = os.path.join(group_path, GROUP_CFG_FN)

    if not group_path.endswith("/"):
        group_path += "/"

    if os.path.exists(group_path):
        logging.critical(f"Group {name} already exists (at {group_path}, aborting")
        sys.exit(1)

    os.makedirs(group_path)

    group_cfg_data = GROUP_CFG_DATA.copy()
    group_cfg_data["dest_path"] = dest_path
    group_cfg_data["desc"]      = group_desc

    logging.debug(f"Creating group cfg file at {group_cfg_path}")
    with open(group_cfg_path, "w+") as f:
        toml.dump(group_cfg_data, f)

    print(f"Successfully created new group {name} (at {group_path})")
    if dest_path == NOT_CONFIGURED:
        logging.warning("Destination folder not configured")
        print(f"Make sure to configure it in {group_cfg_path} before using this group")
    else:
        print(dest_path)
        if os.path.exists(dest_path):
            print(f"File exists at {dest_path}")
            chosen = False
            while not chosen:
                choice = input(
                    "(i)nstall existing config into groups folder, (d)elete the existing file/folder, or (a)bort?"
                )

                match choice.lower():
                    case "i":
                        chosen = True
                        name_valid = False
                        current_name = ""
                        while not name_valid:
                            current_name = input(
                                "What should this config be installed as?\n>"
                            )
                            name_valid = validate_name(current_name, auto_exit=False)

                        installed_path = os.path.join(group_path, current_name)
                        confirm_call(shutil.move, dest_path, installed_path)
                        print(f"Successfully installed config '{current_name}' to group '{name}'")
                    case "d":
                        chosen = True
                        confirm_call(shutil.rmtree, dest_path)
                        print("Successfully deleted existing config")
                    case "a":
                        chosen = True
                        print("Aborting")
                        print("WARNING: Aborting now leaves a group config behind.")
                        print(
                            "There is a file at this config's destination, causing it to error if used."
                        )
                        print(
                            "You can either choose to delete the group now, or keep the group, and remove"
                        )
                        print(
                            "The file/folder at the group's destination manually before using."
                        )
                        if confirm("Delete group?"):
                            group_path = expand_path(group_path)
                            shutil.rmtree(group_path)
                            print(f"Successfully deleted new group {name} and aborted")
                        else:
                            print(f"Leaving existing config and aborting")
                    case "_":
                        print("Please choose i, d, or a")


def command_delete(name: str):
    """Deletes a group given the name"""
    validate_name(name)
    group_path = get_group_path(name)
    if os.path.exists(group_path):
        print(f"Removing group {name} (at {group_path})")
        confirm_call(shutil.rmtree, group_path)
    else:
        logging.critical(
            f"Group {name} doesn't exist (no folder exists at {group_path})"
        )

def dir_size(path: str):
    total_size = 0
    for dirpath, dirnames, filenames in os.walk(path):
        for f in filenames:
            fp = os.path.join(dirpath, f)
            if not os.path.islink(fp):
                total_size += os.path.getsize(fp)

    return total_size

def size_fmt(bytes: int):
    size:float = float(bytes)
    for unit in ["", "K", "M", "G", "T", "P", "E", "Z"]:
        if abs(size) < 1024.0:
            return f"{size:3.1f}{unit}B"
        size /= 1024.0
    return f"{size:.1f}YB"

def command_list(group: str|None):
    """List all of the existing groups"""
    if group is None:
        for group in os.listdir(GROUPS_PATH):
            if group == ".DS_Store": continue
            group_path = os.path.join(GROUPS_PATH, group)
            configs_count = 0
            has_group_config = False
            group_cfg_data = {"desc": "", "dest_path": NOT_CONFIGURED}
            for config in os.listdir(group_path):
                if config == "group.toml":
                    has_group_config = True
                    group_cfg_data = toml.load(os.path.join(group_path, "group.toml"))
                else:
                    configs_count += 1

            msg = f"* {group}"
            if (desc:=group_cfg_data['desc']) != "":
                msg+= f" - {desc}"
            msg += f" | {configs_count} config(s)"
            msg += f" @ {group_path}"
            msg += f" \N{RIGHTWARDS ARROW} swaps to {group_cfg_data['dest_path']}"

            print(msg, end="")

            if not has_group_config:
                print(" | Warning: group is missing 'group.toml' file")
            else:
                print("") # Add the newline that we were missing from earlier
    else:
        group_path = os.path.join(GROUPS_PATH, group)
        group_cfg_data = {"desc": "", "dest_path": NOT_CONFIGURED}
        configs_count = 0
        outstr = ""
        for config in os.listdir(group_path):
            if config == "group.toml":
                has_group_config = True
                group_cfg_data = toml.load(os.path.join(group_path, "group.toml"))
            else:
                if config == ".DS_Store": continue
                config_path = os.path.join(group_path, config)
                config_size = dir_size(config_path)
                outstr += f" * {config} @ {config_path} : {size_fmt(config_size)}\n"
                configs_count += 1

        msg = group
        if (desc:=group_cfg_data['desc']) != "":
            msg+= f" - {desc}"
        msg += f" \N{RIGHTWARDS ARROW} swaps to {group_cfg_data['dest_path']}"
        msg += f"\n{configs_count} config(s):"
        msg += f"\n{outstr}"
        print(msg, end="")

def command_fix(verbose: bool):
    """Fix missing fields in 'group.toml' files"""
    for group in os.listdir(GROUPS_PATH):
        if verbose:
            print(f"Fixing {group}...")
        group_path = os.path.join(GROUPS_PATH, group)
        changes_made = False
        group_cfg_path = os.path.join(group_path, GROUP_CFG_FN)
        try:
            group_cfg_data = toml.load(group_cfg_path)
        except FileNotFoundError:
            if verbose:
                print(f"No config file was found at {group_cfg_path}. Creating it.")
            changes_made = True
            group_cfg_data = GROUP_CFG_DATA.copy()
        for key, value in GROUP_CFG_DATA.items():
            if not key in group_cfg_data:
                if verbose:
                    print(f"Field {key} not found. Adding it.")
                group_cfg_data[key] = value
                changes_made = True

        if changes_made:
            if verbose:
                print(f"Writing fixes for '{group_cfg_path}'.")
            with open(group_cfg_path, "w+") as f:
                toml.dump(group_cfg_data, f)
        else:
            if verbose:
                print(f"No fixes were found for group {group}.")

def command_configure(group: str):
    group_path = os.path.join(GROUPS_PATH, group)
    group_cfg_path = os.path.join(group_path, GROUP_CFG_FN)
    try:
        group_cfg_data = toml.load(group_cfg_path)
    except FileNotFoundError:
        logging.critical(f"No config file was found at {group_cfg_path}")
        print("Try running\n    $ [conswap] fix\nto automatically create it")
        sys.exit(1)

    print("Welcome to the conswap group configuration wizard.")
    print("For each field in the group.toml file, you will be prompted to either:")
    print("    * Type a new value and press enter")
    print("    * Press ctrl+d to keep the value the same")
    for key in group_cfg_data:
        value = group_cfg_data[key]
        print(f"'{key}'='{value}'")
        try:
            new_value = input(">")
            print(f"Updated: '{key}'='{new_value}'")
        except EOFError:
            new_value = value
            print("[ctrl+d]\nValue not updated")
        group_cfg_data[key] = new_value

    print(f"Configuration complete. Writing to {group_cfg_path}")
    with open(group_cfg_path, "w") as f:
        toml.dump(group_cfg_data, f)

def command_swap(group: str, config: str):
    """Swap configs for a certain group"""
    print(f"Swapping group '{group}' to config '{config}'")
    validate_name(group)
    group_path = os.path.join(GROUPS_PATH, group)
    has_group_config = False
    configs = []
    for i in os.listdir(group_path):
        if i == "group.toml":
            has_group_config = True
        else:
            configs.append(i)

    if not has_group_config:
        logging.critical(f"Group {group} is missing group.toml file")
        print("Please create a new group and copy the group.toml")
        print("exitting.")
        return

    if not config in configs:
        logging.critical(f"Config {config} does not exist in group {group}, exitting.")
        return

    group_cfg_path = os.path.join(group_path, "group.toml")
    config_path = os.path.join(group_path, config)

    group_cfg_data = toml.load(group_cfg_path)
    if not "dest_path" in group_cfg_data:
        logging.critical(f"Field 'dest_path' is not defined in group.toml")
        print(f"Please set it in {group_cfg_path}")
        print("exitting.")
        return
    dest_path = group_cfg_data["dest_path"]
    if dest_path == NOT_CONFIGURED:
        logging.critical(f"Field 'dest_path' is not configured in group.toml")
        print(f"Please set it in {group_cfg_path}")
        print("exitting.")
        return
    if os.path.exists(dest_path):
        if os.path.islink(dest_path):
            print("Found previously swapped config; removing it.")
            confirm_call(os.unlink, dest_path)
        else:
            print("Config already exists at destination path")
            chosen = False
            while not chosen:
                choice = input(
                    "(i)nstall existing config into groups folder, (d)elete "
                    "the existing file/folder, or (a)bort?"
                )
                match choice.lower():
                    case "i":
                        chosen = True
                        name_valid = False
                        current_name = ""
                        while not name_valid:
                            current_name = input(
                                "What should this config be installed as?\n>"
                            )
                            name_valid = validate_name(current_name, auto_exit=False)

                        installed_path = os.path.join(group_path, current_name)
                        confirm_call(shutil.move, dest_path, installed_path)
                        print(f"Successfully installed config '{current_name}' to group '{group}'")
                    case "d":
                        chosen = True
                        confirm_call(shutil.rmtree, dest_path)
                        print("Successfully deleted existing config")
                    case "a":
                        chosen = True
                        print("Aborting\n"
                            "WARNING: Aborting now leaves a group config behind.\n"
                            "There is a file at this config's destination, \n"
                            " causing it to error if used.\n"
                            "Delete/move the config or run this command again\n"
                            " to choose another option.\n" 
                        )

                    case "_":
                        print("Please choose i, d, or a")

    print("Linking new config")
    confirm_call(os.symlink, config_path, dest_path)
    print(f"Successfully swapped group {group} to config {config}")

def command_install(group: str, source: Literal["local"]|Literal["git"], location: str):
    group_path = os.path.join(GROUPS_PATH, group)
    if not os.path.isdir(group_path):
        logging.critical(f"Group {group} doesn't exist")
        print("Run the 'list' to see existing groups")
        print("or the 'new' command to create it")
        return

    install_under = input("What name should the group be installed under?\n> ")
    install_path = os.path.join(group_path, install_under, "") # Add a trailing slash by joining with an empty string

    if os.path.exists(install_path):
        logging.critical(f"Group {group} already has a config named {install_under}")
        print("Please remove it or choose a different name")
        return

    match source:
        case "local":
            location = expand_path_safe(location)
            confirm_call(shutil.move, location, install_path)
        case "git":
            subprocess.run(["git", "clone", f"{location}", f"{install_path}"])
        case _:
            assert False, f"Unreachable [install source {source}](please report this issue on github)"

def main():
    ap = ArgumentParser(
        prog="conswap", description="manage and swap configuration files"
    )
    ap.add_argument(
        "-d",
        "--debug",
        action="store_true",
        help="Print debug messages",
    )
    subparsers = ap.add_subparsers(
        title="sub-command",
        dest="command",
        help="command to run",
        required=True,
    )

    new_parser = subparsers.add_parser(
        "new",
        help="create a new (empty) group of swappable configs",
    )
    new_parser.add_argument(
        "name",
        help="the name of the group of configs (for example neovim)",
        type=str,
    )
    new_parser.add_argument(
        "-dt",
        "--dest",
        help="path that files will be swapped to",
        type=str,
        default=NOT_CONFIGURED,
    )

    new_parser.add_argument(
        "-dc",
        "--desc",
        help="group description (optional)",
        type=str,
        default="",
    )

    delete_parser = subparsers.add_parser(
        "delete",
        help="delete a group of configs",
    )
    delete_parser.add_argument(
        "name",
        help="the name of the group to be deleted",
        type=str,
    )

    list_parser = subparsers.add_parser(
        "list",
        help="list existing groups",
    )

    list_parser.add_argument(
        "-g",
        "--group",
        help="group to list configs for (none means list groups)",
    )

    list_parser.add_argument(
        "-v",
        "--verbose",
        help="make the list command show more details",
        action="store_true",
    )

    fix_parser = subparsers.add_parser(
        "fix",
        help="automatically fill in missing fields in 'group.toml' files",
    )

    fix_parser.add_argument(
        "-v",
        "--verbose",
        help="make the fix command show more details",
        action="store_true",
    )

    configure_parser = subparsers.add_parser(
        "configure",
        help="configure settings of a group"
    )

    configure_parser.add_argument(
        "name",
        help="the name of the group to configure",
        type=str,
    )

    swap_parser = subparsers.add_parser(
        "swap",
        help="swap between configs",
    )

    swap_parser.add_argument(
        "group",
        help="name of the config group to swap",
    )

    swap_parser.add_argument(
        "config",
        help="name of the new config in the group to swap to"
    )

    install_parser = subparsers.add_parser(
        "install",
        help="install a new config to an existing group",
    )

    install_parser.add_argument(
        "group",
        help="name of the config group to install to",
    )

    install_parser.add_argument(
        "source",
        choices=["local", "git"],
        help="source of the config (local files or a remote git repository)",
    )

    install_parser.add_argument(
        "location",
        type=str,
        help="location of the config (path of file/folder or url of git repo)",
    )

    args = ap.parse_args()

    if args.debug:
        log_level = logging.DEBUG
    else:
        log_level = logging.INFO

    logging.basicConfig(
        format="%(levelname)s: %(msg)s",
        level=log_level,
    )

    ensure_config_dir()

    try:
        match args.command:
            case "new":
                command_new(args.name, args.dest, args.desc)
            case "delete":
                command_delete(args.name)
            case "list":
                command_list(args.group)
            case "fix":
                command_fix(args.verbose)
            case "configure":
                command_configure(args.name)
            case "swap":
                command_swap(args.group, args.config)
            case "install":
                command_install(args.group, args.source, args.location)
            case _:
                assert False, f"Unreachable [command {args.command}](please report this issue on github)"
    except KeyError:
        logging.critical(f"Subcommand {args.command} crashed.")
        print("It appears that one or more group has a malformed 'group.toml' file.")
        print("Try running\n    $ [conswap] fix\nto add missing fields to config files.")
        print("After running `fix`, you can (optionally) run\n    $ [conswap] configure <group>")
        print("to manually set the fields in the group's 'group.toml' file.")
        print("Don't worry, this error is completely normal after a conswap update.")
        print("This also might have occurred because you made a mistake manually editing the file.")


if __name__ == "__main__":
    main()

