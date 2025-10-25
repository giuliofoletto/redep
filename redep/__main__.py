"""
Allow redep to be executable through `python -m redep`.

Authors: Giulio Foletto.
License: See project-level license file.
"""

from redep.util import configure_logging
from redep.cli import cli


def main():
    configure_logging()
    cli()


if __name__ == "__main__":
    main()
