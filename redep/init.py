import logging


def init(config_path):
    """
    Initialize a new redep configuration file at the specified path.
    """
    if config_path.exists():
        logging.error(f"The configuration file '{config_path}' already exists.")
        return
    # create parent directories if they don't exist
    config_path.parent.mkdir(parents=True, exist_ok=True)
    file_name = config_path.name
    default_configuration_string = f"""
    # redep configuration file
root_dir = "./"  # In most cases, keep as is. This is interpreted as the directory where this config file is located.

match = ["*", "**/*"]  # In most cases, keep as is. This matches everything in the root_dir.

ignore = ["./{str(file_name).replace("\\", "/")}"]
    
[[remotes]]
host = ""  # Replace with remote host or leave empty for local operations.
path = "./"  # Replace with path on the host. For local operations, this can be relative to root_dir.
    """
    with open(config_path, "w") as config_file:
        config_file.write(default_configuration_string.strip())
    logging.info(f"Initialized new redep configuration at: {config_path}")
