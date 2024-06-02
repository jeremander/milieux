from pathlib import Path
import sys

from loguru import logger


__version__ = '0.1.0'

# name of the main executable
PROG = 'milieux'

# path to package root
PKG_DIR = Path(__file__).parent
PKG_NAME = PKG_DIR.name

LOG_FMT = '<level>{time:YYYY-MM-DD HH:mm:ss} - {message}</level>'
logger.remove()
logger.add(sys.stderr, colorize=True, format=LOG_FMT, level='INFO')
logger.level('INFO', color='', icon='')
