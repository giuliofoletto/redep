import glob
import logging
from pathlib import Path, PurePosixPath, PureWindowsPath
import tomllib

import fabric
import shutil


def push(config_file):
    config = tomllib.loads(Path(config_file).read_text())
    ignores = config.get("ignore", [])
    destinations = config.get("destinations", [])
    root_dir = Path(config_file).parent
    logging.info(f"Root directory determined as: {root_dir}")
    selected_files, ignored_files = select_files(root_dir, ignores)
    if len(selected_files) == 0:
        logging.info("No files to push after applying ignore rules.")
        return
    else:
        logging.info(
            "Files to be pushed: "
            + ", ".join(sorted({str(file) for file in selected_files}))
        )
    if len(ignored_files) > 0:
        logging.info(
            "Ignored files: " + ", ".join(sorted({str(file) for file in ignored_files}))
        )

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
            push_local(selected_files, root_dir, Path(path))
        else:
            logging.info(f"Pushing to remote destination: {host}:{path}")
            push_remote(selected_files, root_dir, host, Path(path))

    logging.info("Push operation completed.")


def select_files(root_dir, ignore_patterns):
    all_files = set(
        glob.glob(str(root_dir / "**" / "*"), recursive=True, include_hidden=True)
    )
    ignored_files = [
        set(glob.glob(str(root_dir / pattern), recursive=True, include_hidden=True))
        for pattern in ignore_patterns
    ]
    ignored_files = set().union(*ignored_files)
    # remove directories
    all_files = {Path(f) for f in all_files if Path(f).is_file()}
    ignored_files = {Path(f) for f in ignored_files if Path(f).is_file()}
    selected_files = all_files - ignored_files
    return selected_files, ignored_files


def push_remote(files, root_dir, host, path):
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

    # push files
    for file_path in files:
        relative_path = file_path.relative_to(root_dir)
        if remote_os == "windows":
            remote_path = PureWindowsPath(path / str(relative_path).replace("/", "\\"))
        else:
            remote_path = PurePosixPath(path / str(relative_path).replace("\\", "/"))
        remote_dir = remote_path.parent
        logging.info(f"Creating remote directory: {remote_dir}")
        conn.run(f"mkdir -p '{remote_dir}'")
        if not file_path.is_file():
            logging.warning(f"Skipping {str(file_path)} as it is not a file.")
            continue
        logging.info(f"Uploading {str(file_path)} to {host}:{remote_path}")
        conn.put(file_path, str(remote_path))


def push_local(files, root_dir, path):
    # if path starts with ~, expand it
    if str(path).startswith("~"):
        path = Path.home() / str(path)[2:]

    # if path is relative, make it absolute with respect to root_dir
    if not path.is_absolute():
        path = root_dir / path

    for file_path in files:
        relative_path = file_path.relative_to(root_dir)
        destination_path = path / relative_path
        destination_dir = destination_path.parent
        logging.info(f"Creating local directory: {destination_dir}")
        destination_dir.mkdir(parents=True, exist_ok=True)
        if not Path(file_path).is_file():
            logging.warning(f"Skipping {str(file_path)} as it is not a file.")
            continue
        logging.info(f"Copying {str(file_path)} to {destination_path}")
        shutil.copyfile(file_path, destination_path)
