import logging

import fabric


def push(config_file):
    logging.info(f"Push function called with config file: {config_file}")
