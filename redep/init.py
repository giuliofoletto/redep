import logging


def init(config_path):
    """
    Initialize a new redep configuration file at the specified path.
    """
    if config_path.exists():
        logging.error(f"The configuration file '{config_path}' already exists.")
        return
    file_name = config_path.name
    default_configuration_string = f"""
    # redep configuration file    
ignore = ["./{str(file_name).replace("\\", "/")}"]
    
[[destinations]]
host = ""  # Replace with remote host or leave empty for local push
path = "./"  # Replace with destination path on the host. For local push, this is relative to the directory of the config file.
    """
    with open(config_path, "w") as config_file:
        config_file.write(default_configuration_string.strip())
    logging.info(f"Initialized new redep configuration at: {config_path}")
