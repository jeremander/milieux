import pathlib
from tempfile import TemporaryDirectory

import pytest

from milieux.config import Config, user_default_base_dir, user_default_config_path, user_dir


@pytest.fixture()
def tmp_config(monkeypatch):
    """Fixture to set the user's home directory and  global config's `base_dir` to temporary directories."""
    with TemporaryDirectory() as tmpdir:
        home_dir = pathlib.Path(tmpdir) / 'home'
        home_dir.mkdir()
        monkeypatch.setattr('pathlib.Path.home', lambda: home_dir)
        user_dir().mkdir()
        user_default_base_dir().mkdir()
        cfg = Config()  # default configs
        with cfg.as_config():
            cfg_path = user_default_config_path()
            cfg.save(cfg_path)
            yield cfg
