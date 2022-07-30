"""Manage and swap configuration files

This module isn't intended to be imported, it is a CLI tool."""

import logging
from argparse import ArgumentParser
import os
import pathlib
import sys
from typing import Callable
import toml
import shutil


CONFIG_PATH_SUFFIX = ".config/confman"
GROUPS_SUFFIX = "groups"
CONFIG_PATH = os.path.join(pathlib.Path.home(), CONFIG_PATH_SUFFIX)
GROUPS_PATH = os.path.join(CONFIG_PATH, GROUPS_SUFFIX)
GROUP_CFG_FN = "group.toml"
NOT_CONFIGURED = "NOT CONFIGURED"


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


def command_new(name: str, dest_path: str):
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

    group_cfg_data = {
        "dest_path": dest_path,
    }

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

def command_list():
    """List all of the existing groups"""
    for group in os.listdir(GROUPS_PATH):
        group_path = os.path.join(GROUPS_PATH, group)
        configs_count = 0
        has_group_config = False
        for config in os.listdir(group_path):
            if config == "group.toml":
                has_group_config = True
            else:
                configs_count += 1
        print(f"* ({group}): {configs_count} config(s)", end="")
        if not has_group_config:
            print(" | Warning: group is missing 'group.toml' file")
        else:
            print("") # Add the newline that we were missing from earlier

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
        print("Please set it")
        print("exitting.")
        return
    dest_path = group_cfg_data["dest_path"]
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

def main():
    ap = ArgumentParser(
        prog="confman", description="manage and swap configuration files"
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
        "-d",
        "--dest",
        help="path that files will be swapped to",
        type=str,
        default=NOT_CONFIGURED,
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
        help="list existing groups"
    )

    swap_parser = subparsers.add_parser(
        "swap",
        help="swap between configs",
    )

    swap_parser.add_argument(
        "group",
        help="name of the config group to swap"
    )

    swap_parser.add_argument(
        "config",
        help="name of the new config in the group to swap to"
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

    match args.command:
        case "new":
            command_new(args.name, args.dest)
        case "delete":
            command_delete(args.name)
        case "list":
            command_list()
        case "swap":
            command_swap(args.group, args.config)
        case _:
            assert False, f"Unreachable [command {args.command}](please report this issue on github)"


if __name__ == "__main__":
    main()

