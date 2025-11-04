"""
Allow redep to be executable through `python -m redep`.

Authors: Giulio Foletto.
License: See project-level license file.
"""

from redep.cli import cli
from redep.util import configure_logging


def main():
    configure_logging()
    cli()


if __name__ == "__main__":
    main()
