import logging
import sys

logger = logging.getLogger('waitingserver')
logger.setLevel(logging.DEBUG)

file_handler = logging.FileHandler(filename='waitingserver.log')
console_handler = logging.StreamHandler(sys.stderr)
formatter = logging.Formatter('[%(asctime)s %(levelname)s]: [%(name)s] %(message)s')
console_handler.setFormatter(formatter)
file_handler.setFormatter(formatter)
logger.addHandler(console_handler)
logger.addHandler(file_handler)
