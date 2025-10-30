import glob
import logging
from pathlib import Path, PurePosixPath, PureWindowsPath

import fabric
import shutil


def push(root_dir, matches, ignores, destinations):
    logging.info(f"Root directory determined as: {root_dir}")
    selected_files, selected_dirs, ignored_files, ignored_dirs = select_patterns(
        root_dir, matches, ignores
    )
    if len(selected_files) > 0:
        logging.info(
            "Selected files: "
            + ", ".join(sorted({str(file) for file in selected_files}))
        )
    if len(selected_dirs) > 0:
        logging.info(
            "Selected directories: "
            + ", ".join(sorted({str(dir) for dir in selected_dirs}))
        )
    if len(ignored_files) > 0:
        logging.info(
            "Ignored files: " + ", ".join(sorted({str(file) for file in ignored_files}))
        )
    if len(ignored_dirs) > 0:
        logging.info(
            "Ignored directories: "
            + ", ".join(sorted({str(dir) for dir in ignored_dirs}))
        )
    if len(selected_files) == 0 and len(selected_dirs) == 0:
        logging.warning("No files or directories selected for push; aborting.")
        return

    for destination in destinations:
        host = destination.get("host", None)
        path = destination.get("path", None)
        if host is None or path is None:
            logging.warning(
                f"Skipping destination with missing host or path: {destination}"
            )
            continue
        if host == "":
            # interpret as local push (which is not the same as connection to localhost)
            if path == "":
                # interpret as . (which will be treated as relative path with respect to root_dir)
                path = "."
            logging.info(f"Pushing to local system at: {path}")
            push_local(selected_files, selected_dirs, root_dir, Path(path))
        else:
            logging.info(f"Pushing to remote destination: {host}:{path}")
            push_remote(selected_files, selected_dirs, root_dir, host, Path(path))

    logging.info("Push operation completed.")


def select_patterns(root_dir, match_patterns, ignore_patterns):
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


def push_remote(files, dirs, root_dir, host, path):
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
        remote_os = "windows"
        logging.warning(f"Remote host '{host}' does not seem to be a POSIX system.")
    else:
        remote_os = result.stdout.strip()
        logging.info(f"Remote host '{host}' is running: {remote_os}")

    # if path starts with ~, expand it
    if remote_os == "windows":
        if str(path).startswith("~"):
            path = (
                PureWindowsPath(
                    conn.run("echo %USERPROFILE%", hide=True).stdout.strip()
                )
                / str(path)[2:]
            )
        path = PureWindowsPath(str(path).replace("/", "\\"))  # TODO find better way

    else:
        if str(path).startswith("~"):
            path = (
                PurePosixPath(conn.run("echo $HOME", hide=True).stdout.strip())
                / str(path)[2:]
            )
        path = PurePosixPath(str(path).replace("\\", "/"))  # TODO find better way

    # reduce the directories to include only leaves
    dirs = select_leaf_directories(dirs)
    # create dirs
    for dir_path in dirs:
        relative_path = dir_path.relative_to(root_dir)
        if remote_os == "windows":
            remote_dir = PureWindowsPath(path / str(relative_path).replace("/", "\\"))
        else:
            remote_dir = PurePosixPath(path / str(relative_path).replace("\\", "/"))
        logging.info(f"Creating remote directory: {remote_dir}")
        conn.run(f"mkdir -p '{remote_dir}'")
    # push files
    for file_path in files:
        relative_path = file_path.relative_to(root_dir)
        if remote_os == "windows":
            remote_path = PureWindowsPath(path / str(relative_path).replace("/", "\\"))
        else:
            remote_path = PurePosixPath(path / str(relative_path).replace("\\", "/"))
        logging.info(f"Uploading {str(file_path)} to {host}:{remote_path}")
        conn.put(file_path, str(remote_path))


def push_local(files, dirs, root_dir, path):
    # if path starts with ~, expand it
    if str(path).startswith("~"):
        path = Path.home() / str(path)[2:]

    # if path is relative, make it absolute with respect to root_dir
    if not path.is_absolute():
        path = root_dir / path

    # if path coincides with root_dir, no need to push
    if path == root_dir:
        logging.info("Destination path coincides with root directory; no files pushed.")
        return

    # reduce the directories to include only leaves
    dirs = select_leaf_directories(dirs)
    # create dirs
    for dir_path in dirs:
        relative_path = dir_path.relative_to(root_dir)
        destination_dir = path / relative_path
        logging.info(f"Creating local directory: {destination_dir}")
        destination_dir.mkdir(parents=True, exist_ok=True)
    # push files
    for file_path in files:
        relative_path = file_path.relative_to(root_dir)
        destination_path = path / relative_path
        logging.info(f"Copying {str(file_path)} to {destination_path}")
        shutil.copyfile(file_path, destination_path)


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
