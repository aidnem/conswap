"""Manage and swap configuration files

This module isn't intended to be imported, it is a CLI tool."""

import logging
from argparse import ArgumentParser
import os
import pathlib
import sys
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


def confirm_call(func, *args):
    """Call a function with given arguments after making user confirm"""
    print(
        f"OK to call function '{func.__name__}' with args {args}? This might delete or destroy the file/folder."
    )
    if input("y/N").lower() == "y":
        func(*args)
        return

    logging.critical("Function call aborted, exitting")
    sys.exit()


def validate_name(name):
    """Ensure that a name is valid (letters, numbers, and _ only)"""
    for c in name:
        if not (c.isalnum() or c == "_"):
            logging.critical(
                f"Character {c} is not allowed in group name (must be letters, numbers, or '_')"
            )
            sys.exit(1)


def get_group_path(name: str) -> str:
    """Get the path to a group given the name of the group"""
    validate_name(name)
    group_path = os.path.join(GROUPS_PATH, name)
    return group_path


def command_new(name: str, dest_path: str):
    """Creates a new group given the name"""
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
        if os.path.exists(dest_path):
            print(f"File exists at {dest_path}")


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


if __name__ == "__main__":
    main()
