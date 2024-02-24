import logging
import os

def getLogger(name=__name__):
    logger = logging.getLogger(name)
    if logger.hasHandlers():
        logger.handlers.clear()
    logger.setLevel(logging.DEBUG if os.environ.get('DEBUG') == 'true' else logging.INFO)
    consoleHandler = logging.StreamHandler()
    formatter = logging.Formatter('%(asctime)s [%(levelname)s] (%(name)s) %(message)s')
    consoleHandler.setFormatter(formatter)
    logger.addHandler(consoleHandler)
    return logger