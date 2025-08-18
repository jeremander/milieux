import pytest

from milieux.package import _parse_package_from_requirements


@pytest.mark.parametrize(['line', 'output'], [
    ('', None),
    ('   ', None),
    ('pkg', 'pkg'),
    ('  pkg   ', 'pkg'),
    ('# pkg', None),
    ('   # pkg ', None),
    ('pkg # comment', 'pkg'),
    ('pkg#comment', 'pkg'),
    ('#pkg#comment', None),
    ('pkg >= 1.2.3', 'pkg >= 1.2.3'),
    ('pkg >= 1.2.3  # latest version', 'pkg >= 1.2.3'),
])
def test_parse_package_from_requirements(line, output):
    """Tests the _parse_package_from_requirements helper function."""
    assert _parse_package_from_requirements(line) == output
