"""
Main script to run the application, contains user interface.

Authors: Giulio Foletto.
License: See project-level license file.
"""

import logging
from pathlib import Path

import click

from redep.util import (
    configure_logging,
)
from redep.push import push


@click.group(invoke_without_command=True)
def cli():
    configure_logging()


@cli.command(name="push")
@click.argument("config_path", type=click.Path(), required=False)
def push_command(config_path):
    config_file = None
    # Check if config_path is provided
    if config_path:
        # Check if the path exists
        path = Path(config_path)
        if not path.exists():
            logging.error(f"The specified path '{config_path}' does not exist.")
            return
        else:
            # Check if it's a file or directory
            if path.is_file():
                config_file = path
                logging.info(f"Running with configuration file: {config_file}")
            elif path.is_dir():
                # Look for a config file in the directory
                config_file = path / "redep.toml"
                if config_file.exists():
                    logging.info(f"Running with configuration file: {config_file}")
                else:
                    logging.error(
                        f"No configuration file found in directory '{config_path}'."
                    )
                    return
    else:
        # Run as if the user implied the current directory
        path = Path.cwd()
        # Look for a config file in the directory
        config_file = path / "redep.toml"
        if config_file.exists():
            logging.info(f"Running with configuration file: {config_file}")
        else:
            logging.error(f"No configuration file found in the current directory.")
            return
    push(config_file)
