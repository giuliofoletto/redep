import logging
from pathlib import Path, PurePosixPath, PureWindowsPath
from threading import Thread

import fabric
import shutil

from redep.util import select_patterns, select_leaf_directories


def push(root_dir, matches, ignores, destinations):
    logging.debug(f"Root directory determined as: {root_dir}")
    selected_files, selected_dirs, ignored_files, ignored_dirs = select_patterns(
        root_dir, matches, ignores
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
        logging.warning("No files or directories selected for push; aborting.")
        return

    threads = []
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
            new_thread = Thread(
                target=push_local,
                args=(selected_files, selected_dirs, root_dir, Path(path)),
            )
            new_thread.start()
            threads.append(new_thread)
        else:
            new_thread = Thread(
                target=push_remote,
                args=(selected_files, selected_dirs, root_dir, host, Path(path)),
            )
            new_thread.start()
            threads.append(new_thread)
    for t in threads:
        t.join()
    logging.info("All push operations completed.")


def push_remote(files, dirs, root_dir, host, path):
    logging.info(f"Pushing to remote destination: {host}:{path}")
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
        logging.debug(f"Creating remote directory: {remote_dir}")
        conn.run(f"mkdir -p '{remote_dir}'")
    # push files
    for file_path in files:
        relative_path = file_path.relative_to(root_dir)
        if remote_os == "windows":
            remote_path = PureWindowsPath(path / str(relative_path).replace("/", "\\"))
        else:
            remote_path = PurePosixPath(path / str(relative_path).replace("\\", "/"))
        logging.debug(f"Uploading {str(file_path)} to {host}:{remote_path}")
        conn.put(file_path, str(remote_path))
    logging.info(f"Completed push to remote destination: {host}:{path}")


def push_local(files, dirs, root_dir, path):
    logging.info(f"Pushing to local system at: {path}")
    # if path starts with ~, expand it
    if str(path).startswith("~"):
        path = Path.home() / str(path)[2:]

    # if path is relative, make it absolute with respect to root_dir
    if not path.is_absolute():
        path = root_dir / path

    # if path coincides with root_dir, no need to push
    if path == root_dir:
        logging.warning(
            "Destination path coincides with root directory; no files pushed."
        )
        return

    # reduce the directories to include only leaves
    dirs = select_leaf_directories(dirs)
    # create dirs
    for dir_path in dirs:
        relative_path = dir_path.relative_to(root_dir)
        destination_dir = path / relative_path
        logging.debug(f"Creating local directory: {destination_dir}")
        destination_dir.mkdir(parents=True, exist_ok=True)
    # push files
    for file_path in files:
        relative_path = file_path.relative_to(root_dir)
        destination_path = path / relative_path
        logging.debug(f"Copying {str(file_path)} to {destination_path}")
        shutil.copyfile(file_path, destination_path)
    logging.info(f"Completed push to local system at: {path}")
