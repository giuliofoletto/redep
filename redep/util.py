"""
Shared utility functions.

Authors: Giulio Foletto.
License: See project-level license file.
"""

import logging
import sys

from pathlib import Path
import tomllib


def configure_logging():
    logging.basicConfig(
        stream=sys.stdout,
        level=logging.INFO,
        format="[%(asctime)s] %(levelname)s - %(message)s",
        datefmt="%Y-%m-%dT%H:%M:%S",
    )  # Note that time (and hence default logger) does not support %f


def find_existing_config(starting_path=None):
    result_path = None
    # Check if starting_path is provided
    if starting_path:
        # Check if the path exists
        result_path = Path(starting_path)
        if not result_path.exists():
            logging.error(f"The specified path '{starting_path}' does not exist.")
            return None
        else:
            # Check if it's a file or directory
            if result_path.is_file():
                logging.info(f"Running with configuration file: {result_path}")
            elif result_path.is_dir():
                # Look for a config file in the directory
                result_path = result_path / "redep.toml"
                if result_path.exists():
                    logging.info(f"Running with configuration file: {result_path}")
                else:
                    logging.error(
                        f"No configuration file found in directory '{result_path.parent}'."
                    )
                    return None
    else:
        # Run as if the user implied the current directory
        result_path = Path.cwd() / "redep.toml"
        if result_path.exists():
            logging.info(f"Running with configuration file: {result_path}")
        else:
            logging.error(f"No configuration file found in the current directory.")
            return None
    return result_path


def find_path_new_config(starting_path=None):
    result_path = None
    if starting_path:
        result_path = Path(starting_path)
        if result_path.exists() and result_path.is_dir():
            return result_path / "redep.toml"
        elif result_path.exists() and result_path.is_file():
            return result_path
        elif not result_path.exists():
            # interpret as new file path
            return result_path
    else:
        result_path = Path.cwd() / "redep.toml"
        return result_path


def read_config_file(config_path):
    config = tomllib.loads(Path(config_path).read_text())
    default_root_dir = Path(config_path).parent
    root_dir = Path(config.get("root_dir", default_root_dir))
    if not root_dir.is_absolute():
        root_dir = (default_root_dir / root_dir).resolve()
    matches = [Path(p) for p in config.get("match", [])]
    ignores = [Path(p) for p in config.get("ignore", [])]
    destinations = config.get("destinations", [])
    for i in range(len(destinations)):
        # make path absolute if host is local
        if (
            "host" in destinations[i]
            and destinations[i]["host"] == ""
            and "path" in destinations[i]
        ):
            destinations[i]["path"] = (
                root_dir / Path(destinations[i]["path"])
            ).resolve()
    return root_dir, matches, ignores, destinations
