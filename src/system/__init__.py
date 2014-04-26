import logging
from shared import LOG_NAME

CONSOLE_LEVEL = logging.DEBUG
FILE_LEVEL = logging.DEBUG

logger = logging.getLogger()
logger.setLevel(logging.DEBUG)

ch = logging.StreamHandler()
ch.setLevel(CONSOLE_LEVEL)
formatter = logging.Formatter(datefmt='%H:%M:%S',fmt="%(asctime)s : %(name)-18s: %(levelname)-8s: %(message)s")
ch.setFormatter(formatter)

fh = logging.FileHandler(LOG_NAME)
fh.setLevel(FILE_LEVEL)
formatter = logging.Formatter(fmt="%(asctime)s: %(name)-18s: %(levelname)-8s: %(message)s")
fh.setFormatter(formatter)

if len(logger.handlers) == 0: #avoid adding handlers againg if this module is imported multiple times
    logger.addHandler(ch)
    logger.addHandler(fh)

logging.raiseExceptions = True


if __name__ == '__main__':
    import os
    logging.shutdown()
    os.remove(LOG_NAME)
    logging.info('whats up?')