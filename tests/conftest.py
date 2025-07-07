from logging import Formatter, StreamHandler
import pathlib
import re
import sys
from tempfile import TemporaryDirectory

import pytest

import milieux
from milieux import DATE_FMT
from milieux.config import Config, user_default_base_dir, user_default_config_path, user_dir
import milieux.distro
import milieux.env
import milieux.utils


@pytest.fixture()
def tmp_config(monkeypatch):
    """Fixture to set the user's home directory and global config's `base_dir` to temporary directories."""
    with TemporaryDirectory() as tmpdir:
        home_dir = pathlib.Path(tmpdir) / 'home'
        home_dir.mkdir()
        monkeypatch.setattr('pathlib.Path.home', lambda: home_dir)
        user_dir().mkdir(parents=True)
        user_default_base_dir().mkdir()
        cfg = Config()  # default configs
        with cfg.as_config():
            cfg_path = user_default_config_path()
            cfg.save(cfg_path)
            yield cfg


def strip_rich_markup(text: str) -> str:
    """Strips off rich markup tags from text."""
    # strip [tag]...[/tag] or [tag]
    return re.sub(r'\[/?[^\]]+\]', '', text)


class PlainFormatter(Formatter):
    """Formatter subclass which strips off rich markup tags from log messages."""

    def format(self, record):
        original = super().format(record)
        return strip_rich_markup(original)


@pytest.fixture(scope='session', autouse=True)
def patch_logger():
    """Patches the global logging handler to use a plain handler instead of a RichHandler, preventing markup/highlighting from being rendered in tests."""
    with pytest.MonkeyPatch.context() as mp:
        handler = StreamHandler()
        handler.setFormatter(PlainFormatter(fmt='%(asctime)s - %(message)s', datefmt=DATE_FMT))
        mp.setattr(milieux.logger.parent, 'handlers', [handler])
        yield


@pytest.fixture(scope='session', autouse=True)
def patch_eprint():
    """Patches the eprint function to use a plain printer instead of the rich console printer, preventing markup/highlighting from being rendered in tests."""
    def _eprint(s, **kwargs) -> None:
        print(strip_rich_markup(s), file=sys.stderr)
    with pytest.MonkeyPatch.context() as mp:
        mp.setattr(milieux.distro, 'eprint', _eprint)
        mp.setattr(milieux.env, 'eprint', _eprint)
        mp.setattr(milieux.utils, 'eprint', _eprint)
        yield
