import logging
from pathlib import Path

from rich.console import Console
from rich.logging import RichHandler
from rich.theme import Theme


__version__ = '0.2.4'

# name of the main executable
PROG = 'milieux'

# path to package root
PKG_DIR = Path(__file__).parent
PKG_NAME = PKG_DIR.name

LOG_FMT = '- %(message)s'
DATE_FMT = '%Y-%m-%d %H:%M:%S'
theme = Theme({'log.time': 'cyan'})

console = Console(stderr=True, theme=theme)
handler = RichHandler(
    omit_repeated_times=False,
    show_level=False,
    show_path=False,
    markup=True,
    console=console,
)
logging.basicConfig(
    level=logging.INFO,
    format=LOG_FMT,
    datefmt=DATE_FMT,
    handlers=[handler]
)
logger = logging.getLogger(PROG)
