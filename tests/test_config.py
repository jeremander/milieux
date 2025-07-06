import pytest

from milieux import PKG_DIR
from milieux.config import PipConfig


def test_pkg_dir_valid():
    """Tests that the root PKG_DIR variable is valid."""
    assert PKG_DIR.exists()

class TestPipConfig:
    """Tests the PipConfig.uv class."""
    @pytest.mark.parametrize(['kwargs', 'uv_args'], [
        (
            {},
            []
        ),
        (
            {'default_index_url': 'example.com'},
            ['--default-index', 'example.com']
        ),
        (
            {'index_urls': []},
            []
        ),
        (
            {'index_urls': ['example1.com', 'example2.com']},
            ['--index', 'example1.com', '--index', 'example2.com']
        ),
        (
            {'default_index_url': 'example.com', 'index_urls': ['example1.com', 'example2.com']},
            ['--default-index', 'example.com', '--index', 'example1.com', '--index', 'example2.com']
        ),
    ])
    def test_uv_args(self, kwargs, uv_args):
        cfg = PipConfig(**kwargs)
        assert cfg.uv_args == uv_args
