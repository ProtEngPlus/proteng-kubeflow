import logging
import os

def getLogger(name=__name__):
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG if os.environ.get('DEBUG') == 'true' else logging.INFO)
    consoleHandler = logging.StreamHandler()
    logger.addHandler(consoleHandler)
    return logger