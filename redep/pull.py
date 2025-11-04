import logging
import shutil
from pathlib import Path, PurePosixPath

from redep.util import (
    expand_home_path_local,
    expand_home_path_remote,
    identify_remote_os,
    open_connection,
    select_leaf_directories,
    select_local_patterns,
    select_remote_patterns,
)


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
        # expand ~ if needed
        path = expand_home_path_local(path)
        selected_files, selected_dirs, ignored_files, ignored_dirs = (
            select_local_patterns(path, matches, ignores)
        )
        if len(selected_files) == 0 and len(selected_dirs) == 0:
            logging.warning("No files or directories selected for pull; aborting.")
            return
        pull_local(selected_files, selected_dirs, path, root_dir)
    else:
        conn = open_connection(host)
        selected_files, selected_dirs, ignored_files, ignored_dirs = (
            select_remote_patterns(conn, path, matches, ignores)
        )
        if len(selected_files) == 0 and len(selected_dirs) == 0:
            logging.warning("No files or directories selected for pull; aborting.")
            return
        pull_remote(conn, selected_files, selected_dirs, path, root_dir)
    logging.info("All pull operations completed.")


def pull_remote(conn, files, dirs, pull_from, pull_to):
    if type(conn) is str:
        # allow passing host instead of connection object
        host = conn
        conn = open_connection(host)
    remote_os = identify_remote_os(conn)
    if remote_os == "windows":
        logging.error(
            "Remote pattern selection on Windows hosts is not yet implemented."
        )  # TODO
        return
    # expand ~ if needed
    pull_from = expand_home_path_remote(conn, pull_from, remote_os)
    logging.info(f"Pulling from remote host: {conn.original_host}:{pull_from}")

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
        logging.debug(
            f"Downloading {conn.original_host}:{str(file_path)} to {destination_path}"
        )
        conn.get(str(file_path), str(destination_path))
    logging.info(f"Completed pull from remote host: {conn.original_host}:{pull_from}")


def pull_local(files, dirs, pull_from, pull_to):
    # expand ~ if needed
    pull_from = expand_home_path_local(pull_from)
    # if pull_from is relative, make it absolute with respect to pull_to (plays the role of root_dir here)
    if not pull_from.is_absolute():
        pull_from = pull_to / pull_from
    # if path coincides with root_dir, no need to push
    if pull_to == pull_from:
        logging.warning("Local source and destination paths coincide; nothing pulled.")
        return
    logging.info(f"Pulling to local system from: {pull_from}")

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
