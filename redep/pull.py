import logging
import shutil
from pathlib import Path, PurePosixPath

import fabric

from redep.util import select_leaf_directories, select_patterns


def pull(root_dir, matches, ignores, source):
    if isinstance(source, list):
        if len(source) > 1:
            logging.warning(
                "Multiple sources specified for pull; only the first will be used."
            )
        source = source[0]
    logging.debug(f"Root directory determined as: {root_dir}")
    host = source.get("host", None)
    path = source.get("path", None)
    if host is None or path is None:
        logging.error(f"Cannot pull from improperly specified host or path: {source}")
        return
    if host == "":
        # interpret as local pull (which is not the same as connection to localhost)
        if path == "":
            # interpret as . (which will be treated as relative path with respect to root_dir)
            path = "."
        if not Path(path).is_absolute():
            path = (root_dir / Path(path)).resolve()
        if str(path).startswith("~"):
            path = Path.home() / str(path)[2:]
        selected_files, selected_dirs, ignored_files, ignored_dirs = select_patterns(
            path, matches, ignores
        )
    else:
        selected_files, selected_dirs, ignored_files, ignored_dirs = (
            select_remote_patterns(host, path, matches, ignores)
        )

    if len(selected_files) > 0:
        logging.debug(
            "Selected files: "
            + ", ".join(sorted({str(file) for file in selected_files}))
        )
    if len(selected_dirs) > 0:
        logging.debug(
            "Selected directories: "
            + ", ".join(sorted({str(dir) for dir in selected_dirs}))
        )
    if len(ignored_files) > 0:
        logging.debug(
            "Ignored files: " + ", ".join(sorted({str(file) for file in ignored_files}))
        )
    if len(ignored_dirs) > 0:
        logging.debug(
            "Ignored directories: "
            + ", ".join(sorted({str(dir) for dir in ignored_dirs}))
        )
    if len(selected_files) == 0 and len(selected_dirs) == 0:
        logging.warning("No files or directories selected for pull; aborting.")
        return

    if host == "":
        pull_local(selected_files, selected_dirs, path, root_dir)
    else:
        pull_remote(host, selected_files, selected_dirs, path, root_dir)

    logging.info("All pull operations completed.")


def pull_remote(host, files, dirs, pull_from, pull_to):
    logging.info(f"Pulling from remote host: {host}:{pull_from}")
    conn = fabric.Connection(host=host)
    # verify if host is reachable
    try:
        conn.open()
    except Exception as e:
        logging.error(f"Could not connect to host '{host}': {e}")
        return
    # check if remote host is posix by running 'uname' command
    result = conn.run("uname -s", hide=True, warn=True)
    remote_os = None
    if result.failed:
        # check if it's windows by running 'ver' command
        result_ver = conn.run("ver", hide=True, warn=True)
        if result_ver.failed:
            logging.warning(
                f"Could not determine operating system of remote host '{host}'; assuming POSIX-compliant."
            )
            remote_os = "posix"
        else:
            remote_os = "windows"
            logging.debug(f"Remote host '{host}' does not seem to be a POSIX system.")
    else:
        remote_os = result.stdout.strip()
        logging.debug(f"Remote host '{host}' is running: {remote_os}")

    if remote_os == "windows":
        logging.error(
            "Remote pattern selection on Windows hosts is not yet implemented."
        )  # TODO
        return

    # Expand ~ if needed
    if str(pull_from).startswith("~"):
        pull_from = (
            PurePosixPath(conn.run("echo $HOME", hide=True).stdout.strip())
            / str(pull_from)[2:]
        )

    # reduce the directories to include only leaves
    dirs = select_leaf_directories(dirs)
    # create dirs
    for dir_path in dirs:
        relative_path = dir_path.relative_to(pull_from)
        destination_dir = pull_to / relative_path
        logging.debug(f"Creating local directory: {destination_dir}")
        destination_dir.mkdir(parents=True, exist_ok=True)
    # pull files
    for file_path in files:
        relative_path = file_path.relative_to(pull_from)
        destination_path = pull_to / relative_path
        logging.debug(f"Pulling {str(file_path)} to {destination_path}")
        conn.get(str(file_path), str(destination_path))
    logging.info(f"Completed pull from remote host: {host}:{pull_from}")


def pull_local(files, dirs, pull_from, pull_to):
    logging.info(f"Pulling to local system from: {pull_from}")
    # if path starts with ~, expand it
    if str(pull_from).startswith("~"):
        pull_from = Path.home() / str(pull_from)[2:]

    # if pull_from is relative, make it absolute with respect to pull_to (plays the role of root_dir here)
    if not pull_from.is_absolute():
        pull_from = pull_to / pull_from

    # if path coincides with root_dir, no need to push
    if pull_to == pull_from:
        logging.warning("Source and destination paths coincide; nothing pushed.")
        return

    # reduce the directories to include only leaves
    dirs = select_leaf_directories(dirs)
    # create dirs
    for dir_path in dirs:
        relative_path = dir_path.relative_to(pull_from)
        destination_dir = pull_to / relative_path
        logging.debug(f"Creating local directory: {destination_dir}")
        destination_dir.mkdir(parents=True, exist_ok=True)
    # push files
    for file_path in files:
        relative_path = file_path.relative_to(pull_from)
        destination_path = pull_to / relative_path
        logging.debug(f"Copying {str(file_path)} to {destination_path}")
        shutil.copyfile(file_path, destination_path)
    logging.info(f"Completed push to local system from: {pull_from}")


def select_remote_patterns(host, root_dir, match_patterns, ignore_patterns):
    conn = fabric.Connection(host=host)
    # verify if host is reachable
    try:
        conn.open()
    except Exception as e:
        logging.error(f"Could not connect to host '{host}': {e}")
        return None, None, None, None
    # check if remote host is posix by running 'uname' command
    result = conn.run("uname -s", hide=True, warn=True)
    remote_os = None
    if result.failed:
        # check if it's windows by running 'ver' command
        result_ver = conn.run("ver", hide=True, warn=True)
        if result_ver.failed:
            logging.warning(
                f"Could not determine operating system of remote host '{host}'; assuming POSIX-compliant."
            )
            remote_os = "posix"
        else:
            remote_os = "windows"
            logging.debug(f"Remote host '{host}' does not seem to be a POSIX system.")
    else:
        remote_os = result.stdout.strip()
        logging.debug(f"Remote host '{host}' is running: {remote_os}")

    if remote_os == "windows":
        logging.error(
            "Remote pattern selection on Windows hosts is not yet implemented."
        )  # TODO
        return None, None, None, None

    # Expand ~ if needed
    if str(root_dir).startswith("~"):
        root_dir = (
            PurePosixPath(conn.run("echo $HOME", hide=True).stdout.strip())
            / str(root_dir)[2:]
        )

    all_files = set()
    for pattern in match_patterns:
        result = conn.run(
            f"find {root_dir} -type f -wholename '{str(root_dir) + "/" + str(pattern).replace("\\", "/")}'",
            hide=True,
            warn=True,
        )
        result = result.stdout.strip().split()
        all_files.update([PurePosixPath(f) for f in result])
    all_dirs = set()
    for pattern in match_patterns:
        result = conn.run(
            f"find {root_dir} -type d -wholename '{str(root_dir) + "/" + str(pattern).replace("\\", "/")}'",
            hide=True,
            warn=True,
        )
        result = result.stdout.strip().split()
        all_dirs.update([PurePosixPath(f) for f in result])
    ignored_files = set()
    for pattern in ignore_patterns:
        result = conn.run(
            f"find {root_dir} -type f -wholename '{str(root_dir) + "/" + str(pattern).replace("\\", "/")}'",
            hide=True,
            warn=True,
        )
        result = result.stdout.strip().split()
        ignored_files.update([PurePosixPath(f) for f in result])
    ignored_dirs = set()
    for pattern in ignore_patterns:
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
