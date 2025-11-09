# Redep

Redep is a simple tool to push and pull a directory to remote hosts or local paths.
It's a simplified way to write `scp` or `rsync` commands, with configuration stored in a TOML file.

## Installation

Clone the repository and install the package using `pip`:

```bash
pip install .
```

This will make the `redep` command-line tool available.

It should work on Windows and Linux systems.
It has not been tested on macOS, but it should work as well.

## Usage

Initialize a configuration file `redep.toml` in the directory you want to work in:

```bash
redep init
```

Add target hosts:

```bash
redep remote add user@host:path/to/destination
```

or edit `redep.toml` in a text editor.
If you only pass a local path (without `user@host:`), it will be treated as a local destination.

Push the directory:

```bash
redep push
```

or pull into the directory:

```bash
redep pull
```

Whenever you change something and want to transfer again, just rerun the push or pull command.

## Status and roadmap

I developed Redep for my personal use, and it works well for my needs.
However, it is still in early development and may lack some features or robustness for broader use.
Sometimes I introduce breaking changes.

## AI use

I program mostly for my own enjoyment and learning, which is why I avoid using fully agentic-style AI tools or vibe-coding.
However, I use AI-assisted autocomplete, and sometimes chat tools to find solutions to specific problems (e.g., how to write scripts in various shell languages).
Several unit tests make heavy use of AI autocomplete, but I've tried to review manually all AI insertions to the best of my abilities.

## Acknowledgements

Redep uses [Fabric](https://www.fabfile.org/) for remote operations.
