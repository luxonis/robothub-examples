import logging as log
import os

import config


def standalone_runtime() -> bool:
    # Checks whether the app is running in standalone mode.
    return os.environ.get('CUPS_APP_RUNTIME') == 'standalone'


def init_logger() -> None:
    # Set the logging level based on the value of LOGGING_LEVEL.
    if config.LOGGING_LEVEL == 0:
        log_level = log.DEBUG
    elif config.LOGGING_LEVEL == 1:
        log_level = log.INFO
    elif config.LOGGING_LEVEL == 2:
        log_level = log.WARNING
    elif config.LOGGING_LEVEL == 3:
        log_level = log.ERROR
    elif config.LOGGING_LEVEL == 4:
        log_level = log.CRITICAL
    else:
        log_level = log.WARNING

    [log.root.removeHandler(handler) for handler in log.root.handlers[:]]
    log.basicConfig(
        format='[%(asctime)s] %(levelname)s [%(processName)s::%(threadName)s] '
               '%(filename)s:%(lineno)s (%(funcName)s) => %(message)s',
        level=log_level
    )
