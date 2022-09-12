import logging
import os
import sys


def build_logger(init_file_name):
    """Init custom logger."""
    logger = logging.getLogger(init_file_name)

    log_filename = "logs/time_measurement.log"
    os.makedirs(os.path.dirname(log_filename), exist_ok=True)

    logging.basicConfig(
        level=logging.DEBUG,
        datefmt="%d %m %y %H:%M:%S",
        format="\n%(asctime)23s :: %(name)-15s :: line %(lineno)5s :: %(message)20s",
        handlers=[
            logging.FileHandler(filename=log_filename, mode="a"),
            # logging.StreamHandler(sys.stdout)
        ]
    )

    return logger
