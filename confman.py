"""Manage and swap configuration files

This module isn't intended to be imported, it is a CLI tool."""

import logging
from argparse import ArgumentParser
import os
import pathlib
import sys


CONFIG_PATH = os.path.join(pathlib.Path.home(), ".config/confman")


def ensure_config_dir():
    if os.path.isdir(CONFIG_PATH):
        logging.debug(f"Found {CONFIG_PATH}")
    else:
        logging.info(f"No config directory was found, creating it in {CONFIG_PATH}")

        os.makedirs(CONFIG_PATH)
        
        if os.path.isdir(CONFIG_PATH):
            logging.debug("Created config directory")
        else:
            logging.critical(f"Failed to create config folder; exitting")
            sys.exit()


def main():
    ap = ArgumentParser(prog="confman",
                        description="Manage and swap configuration files"
    )
    ap.add_argument("-d",
                    "--debug",
                    action="store_true",
                    help="Print debug messages"
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

if __name__ == '__main__':
    main()
