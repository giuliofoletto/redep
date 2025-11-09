"""
Main script to run the application, contains user interface.

Authors: Giulio Foletto.
License: See project-level license file.
"""

import click

from redep.config import init, add_remote, remove_remote
from redep.pull import pull
from redep.push import push
from redep.util import (
    configure_logging,
    find_existing_config,
    find_path_new_config,
    read_config_file,
)


@click.group(invoke_without_command=True)
@click.pass_context
def cli(ctx):
    if ctx.invoked_subcommand is None:
        click.echo(ctx.get_help())
    configure_logging()


@cli.command(name="push")
@click.option("--config", "config", type=click.Path(), required=False)
def push_command(config):
    config_file = find_existing_config(config)
    if config_file:
        root_dir, matches, ignores, remotes = read_config_file(config_file)
        push(root_dir, matches, ignores, remotes)


@cli.command(name="pull")
@click.option("--config", "config", type=click.Path(), required=False)
def pull_command(config):
    config_file = find_existing_config(config)
    if config_file:
        root_dir, matches, ignores, remotes = read_config_file(config_file)
        pull(root_dir, matches, ignores, remotes)


@cli.command(name="init")
@click.option("--config", "config", type=click.Path(), required=False)
def init_command(config):
    path = find_path_new_config(config)
    init(path)


@cli.group(invoke_without_command=True)
@click.pass_context
def remote(ctx):
    if ctx.invoked_subcommand is None:
        click.echo(ctx.get_help())
    configure_logging()


@remote.command()
@click.argument("host_path_string", type=str, required=True)
@click.option("--config", "config", type=click.Path(), required=False)
def add(host_path_string, config):
    path = find_path_new_config(config)
    add_remote(path, host_path_string)


@remote.command()
@click.argument("host_path_string", type=str, required=True)
@click.option("--config", "config", type=click.Path(), required=False)
def rm(host_path_string, config):
    path = find_path_new_config(config)
    remove_remote(path, host_path_string)
