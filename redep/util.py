"""
Shared utility functions.

Authors: Giulio Foletto.
License: See project-level license file.
"""

import glob
import logging
import sys
import tomllib
from pathlib import Path, PurePosixPath, PureWindowsPath

import fabric


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
    remotes = config.get("remotes", [])
    for i in range(len(remotes)):
        # make path absolute if host is local
        if "host" in remotes[i] and remotes[i]["host"] == "" and "path" in remotes[i]:
            remotes[i]["path"] = (root_dir / Path(remotes[i]["path"])).resolve()
    return root_dir, matches, ignores, remotes


def select_local_patterns(root_dir, match_patterns, ignore_patterns):
    all_patterns = [
        set(glob.glob(str(root_dir / pattern), recursive=True, include_hidden=True))
        for pattern in match_patterns
    ]
    all_patterns = set().union(*all_patterns)
    ignored_patterns = [
        set(glob.glob(str(root_dir / pattern), recursive=True, include_hidden=True))
        for pattern in ignore_patterns
    ]
    ignored_patterns = set().union(*ignored_patterns)
    # distinguish files and directories
    all_files = {Path(f) for f in all_patterns if Path(f).is_file()}
    all_dirs = {Path(f) for f in all_patterns if Path(f).is_dir()}
    ignored_files = {Path(f) for f in ignored_patterns if Path(f).is_file()}
    ignored_dirs = {Path(f) for f in ignored_patterns if Path(f).is_dir()}
    selected_files = all_files - ignored_files
    selected_dirs = all_dirs - ignored_dirs
    selected_dirs.add(root_dir)  # always include root_dir
    return selected_files, selected_dirs, ignored_files, ignored_dirs


def select_leaf_directories(directories):
    """Given a set of directories, return only the leaf directories (i.e., those that are not parents of any other directory in the set)."""
    leaf_dirs = set(directories)
    skip = False
    for dir1 in directories:
        for dir2 in directories:
            if dir1 != dir2 and dir2.is_relative_to(dir1):
                if dir1 in leaf_dirs:
                    leaf_dirs.remove(dir1)
                    skip = True
                    break
        if skip:
            skip = False
            continue
    return leaf_dirs


def open_connection(host):
    conn = fabric.Connection(host=host)
    try:
        conn.open()
        return conn
    except Exception as e:
        logging.error(f"Could not connect to host '{host}': {e}")
        raise e


def identify_remote_os(connection):
    result = connection.run("uname -s", hide=True, warn=True)
    remote_os = None
    if result.ok:
        remote_os = result.stdout.strip().lower()
    else:
        # check if it's windows by running 'ver' command
        result_ver = connection.run("ver", hide=True, warn=True)
        if result_ver.ok:
            remote_os = "windows"
        else:
            # assume posix if both commands fail
            remote_os = "posix"
    return remote_os


def expand_home_path_remote(connection, path, remote_os):
    if remote_os == "windows":
        if str(path).startswith("~"):
            path = (
                PureWindowsPath(
                    connection.run("echo %USERPROFILE%", hide=True).stdout.strip()
                )
                / str(path)[2:]
            )
        path = PureWindowsPath(str(path).replace("/", "\\"))  # TODO find better way
    else:
        if str(path).startswith("~"):
            path = (
                PurePosixPath(connection.run("echo $HOME", hide=True).stdout.strip())
                / str(path)[2:]
            )
        path = PurePosixPath(str(path).replace("\\", "/"))  # TODO find better way
    return path


def expand_home_path_local(path):
    if str(path).startswith("~"):
        path = Path.home() / str(path)[2:]
    return path


def select_remote_patterns(conn, root_dir, match_patterns, ignore_patterns):
    if type(conn) is str:
        # allow passing host instead of connection object
        conn = open_connection(conn)
    remote_os = identify_remote_os(conn)

    # expand ~ if needed
    root_dir = expand_home_path_remote(conn, root_dir, remote_os)

    all_files = set()
    for pattern in match_patterns:
        if remote_os == "windows":
            result = conn.run(
                f"PowerShell -Command \"Get-ChildItem -Path {root_dir} -File -Recurse | Where-Object {{ $_.FullName -like \'{str(root_dir / pattern).replace("/", "\\")}\' }} | Select-Object -ExpandProperty FullName\"",
                hide=True,
                warn=True,
            )
            result = result.stdout.strip().split()
            all_files.update([PureWindowsPath(f) for f in result])
        else:
            result = conn.run(
                f"find {root_dir} -type f -wholename '{str(root_dir) + "/" + str(pattern).replace("\\", "/")}'",
                hide=True,
                warn=True,
            )
            result = result.stdout.strip().split()
            all_files.update([PurePosixPath(f) for f in result])
    all_dirs = set()
    for pattern in match_patterns:
        if remote_os == "windows":
            result = conn.run(
                f"PowerShell -Command \"Get-ChildItem -Path {root_dir} -Directory -Recurse | Where-Object {{ $_.FullName -like \'{str(root_dir / pattern).replace("/", "\\")}\' }} | Select-Object -ExpandProperty FullName\"",
                hide=True,
                warn=True,
            )
            result = result.stdout.strip().split()
            all_dirs.update([PureWindowsPath(f) for f in result])
        else:
            result = conn.run(
                f"find {root_dir} -type d -wholename '{str(root_dir) + "/" + str(pattern).replace("\\", "/")}'",
                hide=True,
                warn=True,
            )
            result = result.stdout.strip().split()
            all_dirs.update([PurePosixPath(f) for f in result])
    ignored_files = set()
    for pattern in ignore_patterns:
        if remote_os == "windows":
            result = conn.run(
                f"PowerShell -Command \"Get-ChildItem -Path {root_dir} -File -Recurse | Where-Object {{ $_.FullName -like \'{str(root_dir / pattern).replace("/", "\\")}\' }} | Select-Object -ExpandProperty FullName\"",
                hide=True,
                warn=True,
            )
            result = result.stdout.strip().split()

            ignored_files.update([PureWindowsPath(f) for f in result])
        else:
            result = conn.run(
                f"find {root_dir} -type f -wholename '{str(root_dir) + "/" + str(pattern).replace("\\", "/")}'",
                hide=True,
                warn=True,
            )
            result = result.stdout.strip().split()
            ignored_files.update([PurePosixPath(f) for f in result])
    ignored_dirs = set()
    for pattern in ignore_patterns:
        if remote_os == "windows":
            result = conn.run(
                f"PowerShell -Command \"Get-ChildItem -Path {root_dir} -Directory -Recurse | Where-Object {{ $_.FullName -like \'{str(root_dir / pattern).replace("/", "\\")}\' }} | Select-Object -ExpandProperty FullName\"",
                hide=True,
                warn=True,
            )
            result = result.stdout.strip().split()
            ignored_dirs.update([PureWindowsPath(f) for f in result])
        else:
            result = conn.run(
                f"find {root_dir} -type d -wholename '{str(root_dir) + "/" + str(pattern).replace("\\", "/")}'",
                hide=True,
                warn=True,
            )
            result = result.stdout.strip().split()
            ignored_dirs.update([PurePosixPath(f) for f in result])
    selected_files = all_files - ignored_files
    selected_dirs = all_dirs - ignored_dirs
    selected_dirs.add(root_dir)  # always include root_dir
    return selected_files, selected_dirs, ignored_files, ignored_dirs
