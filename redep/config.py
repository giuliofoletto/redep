import logging
import tomllib
import tomli_w


def init(config_path, config=None):
    """
    Initialize a new redep configuration file at the specified path.
    """
    if config_path.exists():
        logging.error(f"The configuration file '{config_path}' already exists.")
        return
    # create parent directories if they don't exist
    config_path.parent.mkdir(parents=True, exist_ok=True)
    file_name = config_path.name
    if config is None:
        config = {
            "root_dir": "./",
            "match": ["*", "**/*"],
            "ignore": [f"./{str(file_name).replace('\\', '/')}"],
            "remotes": [],
        }
    with open(config_path, "wb") as config_file:
        tomli_w.dump(config, config_file)
    logging.info(f"Initialized new redep configuration at: {config_path}")


def add_remote(config_path, host_path_string):
    """
    Add a new remote to an existing redep configuration file.

    The host_path_string should be in the format 'user@host:/path/to/dir' or
    'host:/path/to/dir' for SSH remotes, or just '/path/to/dir' for local paths.
    """
    if not config_path.exists():
        logging.error(f"The configuration file '{config_path}' does not exist.")
        return
    segments = host_path_string.split(":")
    if len(segments) == 2:
        host = segments[0]
        path = segments[-1]
    elif len(segments) == 1:
        host = ""
        path = segments[0]
    else:
        logging.error(
            f"Invalid remote format '{host_path_string}'. Expected format: 'user@host:/path/to/dir' or 'known_host:/path/to/dir' or '/path/to/dir'."
        )
        return
    with open(config_path, "rb") as config_file:
        config_data = tomllib.load(config_file)
    remotes = config_data.get("remotes", [])
    remotes.append({"host": host, "path": path})
    config_data["remotes"] = remotes
    with open(config_path, "wb") as config_file:
        tomli_w.dump(config_data, config_file)
    logging.info(
        f"Added new remote host = {host}, path = {path} to configuration at: {config_path}"
    )


def remove_remote(config_path, host_path_string):
    """
    Remove a remote from an existing redep configuration file.

    The host_path_string should be in the format 'user@host:/path/to/dir' or
    'known_host:/path/to/dir' for SSH remotes, or just '/path/to/dir' for local paths.
    """
    if not config_path.exists():
        logging.error(f"The configuration file '{config_path}' does not exist.")
        return
    segments = host_path_string.split(":")
    if len(segments) == 2:
        host = segments[0]
        path = segments[-1]
    elif len(segments) == 1:
        host = ""
        path = segments[0]
    else:
        logging.error(
            f"Invalid remote format '{host_path_string}'. Expected format: 'user@host:/path/to/dir' or 'known_host:/path/to/dir' or '/path/to/dir'."
        )
        return
    with open(config_path, "rb") as config_file:
        config_data = tomllib.load(config_file)
    remotes = config_data.get("remotes", [])
    new_remotes = [
        remote
        for remote in remotes
        if not (remote["host"] == host and remote["path"] == path)
    ]
    if len(new_remotes) == len(remotes):
        logging.warning(
            f"No matching remote found for host = {host}, path = {path} in configuration at: {config_path}"
        )
        return
    config_data["remotes"] = new_remotes
    with open(config_path, "wb") as config_file:
        tomli_w.dump(config_data, config_file)
    logging.info(
        f"Removed remote host = {host}, path = {path} from configuration at: {config_path}"
    )


def add_ignore_pattern(config_path, pattern):
    """
    Add a new ignore pattern to an existing redep configuration file.
    """
    if not config_path.exists():
        logging.error(f"The configuration file '{config_path}' does not exist.")
        return
    with open(config_path, "rb") as config_file:
        config_data = tomllib.load(config_file)
    ignores = config_data.get("ignore", [])
    if pattern in ignores:
        logging.warning(
            f"The ignore pattern '{pattern}' already exists in the configuration."
        )
        return
    ignores.append(pattern)
    config_data["ignore"] = ignores
    with open(config_path, "wb") as config_file:
        tomli_w.dump(config_data, config_file)
    logging.info(f"Added ignore pattern '{pattern}' to configuration at: {config_path}")


def remove_ignore_pattern(config_path, pattern):
    """
    Remove an ignore pattern from an existing redep configuration file.
    """
    if not config_path.exists():
        logging.error(f"The configuration file '{config_path}' does not exist.")
        return
    with open(config_path, "rb") as config_file:
        config_data = tomllib.load(config_file)
    ignores = config_data.get("ignore", [])
    if pattern not in ignores:
        logging.warning(
            f"The ignore pattern '{pattern}' does not exist in the configuration."
        )
        return
    ignores.remove(pattern)
    config_data["ignore"] = ignores
    with open(config_path, "wb") as config_file:
        tomli_w.dump(config_data, config_file)
    logging.info(
        f"Removed ignore pattern '{pattern}' from configuration at: {config_path}"
    )
