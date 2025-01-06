import logging
import pathlib

from recipesauto.__about__ import __version__

NAME = "recipesauto"
VERSION = __version__
ROOT_DIR = pathlib.Path(__file__).parent

# logger to use everywhere (not part of Context class because we need it early, before
# Context has been initialized)
logging.basicConfig(
    level=logging.INFO, format="[%(asctime)s: %(levelname)s] %(message)s"
)
logger: logging.Logger = logging.getLogger(NAME)
