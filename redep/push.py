import logging
import shutil
from pathlib import Path, PurePosixPath, PureWindowsPath
from threading import Thread

from redep.util import (
    expand_home_path_local,
    expand_home_path_remote,
    identify_remote_os,
    open_connection,
    select_leaf_directories,
    select_patterns,
)


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


def push_remote(files, dirs, root_dir, conn, path):
    if type(conn) is str:
        # allow passing host instead of connection object
        host = conn
        conn = open_connection(host)
    remote_os = identify_remote_os(conn)
    # expand ~ if needed
    path = expand_home_path_remote(conn, path, remote_os)
    logging.info(f"Pushing to remote destination: {conn.original_host}:{path}")

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
        logging.debug(
            f"Uploading {str(file_path)} to {conn.original_host}:{remote_path}"
        )
        conn.put(file_path, str(remote_path))
    logging.info(f"Completed push to remote destination: {conn.original_host}:{path}")


def push_local(files, dirs, root_dir, path):
    # expand ~ if needed
    path = expand_home_path_local(path)
    # if path is relative, make it absolute with respect to root_dir
    if not path.is_absolute():
        path = root_dir / path
    # if path coincides with root_dir, no need to push
    if path == root_dir:
        logging.warning(
            "Destination path coincides with root directory; nothing pushed."
        )
        return
    logging.info(f"Pushing to local system at: {path}")

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
