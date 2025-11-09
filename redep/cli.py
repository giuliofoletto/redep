"""
Main script to run the application, contains user interface.

Authors: Giulio Foletto.
License: See project-level license file.
"""

import click

from redep.config import (
    init,
    add_remote,
    remove_remote,
    add_ignore_pattern,
    remove_ignore_pattern,
)
from redep.pull import pull
from redep.push import push
from redep.util import (
    configure_logging,
    find_existing_config,
    find_path_new_config,
    read_config_file,
)


class UnexpandablePattern(click.ParamType):
    def convert(self, value, param, ctx):
        return str(value)


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


@remote.command(name="add")
@click.argument("host_path_string", type=str, required=True)
@click.option("--config", "config", type=click.Path(), required=False)
def remote_add(host_path_string, config):
    path = find_path_new_config(config)
    add_remote(path, host_path_string)


@remote.command(name="rm")
@click.argument("host_path_string", type=str, required=True)
@click.option("--config", "config", type=click.Path(), required=False)
def remote_rm(host_path_string, config):
    path = find_path_new_config(config)
    remove_remote(path, host_path_string)


@cli.group(invoke_without_command=True)
@click.pass_context
def ignore(ctx):
    if ctx.invoked_subcommand is None:
        click.echo(ctx.get_help())
    configure_logging()


@ignore.command(name="add")
@click.argument("pattern", type=UnexpandablePattern(), required=True)
@click.option("--config", "config", type=click.Path(), required=False)
def ignore_add(pattern, config):
    path = find_path_new_config(config)
    add_ignore_pattern(path, pattern)


@ignore.command(name="rm")
@click.argument("pattern", type=UnexpandablePattern(), required=True)
@click.option("--config", "config", type=click.Path(), required=False)
def ignore_rm(pattern, config):
    path = find_path_new_config(config)
    remove_ignore_pattern(path, pattern)
