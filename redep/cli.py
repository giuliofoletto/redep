"""
Main script to run the application, contains user interface.

Authors: Giulio Foletto.
License: See project-level license file.
"""

import click

from redep.util import (
    configure_logging,
    find_existing_config,
    find_path_new_config,
    read_config_file,
)
from redep.push import push
from redep.init import init


@click.group(invoke_without_command=True)
def cli():
    configure_logging()


@cli.command(name="push")
@click.argument("config_path", type=click.Path(), required=False)
def push_command(config_path):
    config_file = find_existing_config(config_path)
    if config_file:
        root_dir, matches, ignores, remotes = read_config_file(config_file)
        push(root_dir, matches, ignores, remotes)


@cli.command(name="init")
@click.argument("config_path", type=click.Path(), required=False)
def init_command(config_path):
    path = find_path_new_config(config_path)
    init(path)
