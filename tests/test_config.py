from milieux import PKG_DIR


def test_pkg_dir_valid():
    """Tests that the root PKG_DIR variable is valid."""
    assert PKG_DIR.exists()
