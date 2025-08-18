from pathlib import Path
import re

import pytest

from milieux.errors import InvalidPackageError
from milieux.package import Requirement, _get_requirement_line


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
def test_get_requirement_line(line, output):
    """Tests the _get_requirement_line helper function."""
    assert _get_requirement_line(line) == output

@pytest.mark.parametrize(['req_str', 'is_path', 'err'], [
    (
        'my_pkg',
        False,
        None
    ),
    (
        '.',
        True,
        None
    ),
    (
        '/path/to/pkg',
        True,
        None
    ),
    (
        '-e /path/to/pkg',
        True,
        None
    ),
    (
        '-e file:///path/to/pkg',
        True,
        None
    ),
    (
        'my_pkg==1.2',
        False,
        None
    ),
    (
        'my_pkg == 1.2',
        False,
        None
    ),
    (
        'my_pkg>1.2',
        False,
        None
    ),
    (
        'my_pkg > 1.2',
        False,
        None
    ),
    (
        'my_pkg[extra]',
        False,
        None
    ),
    (
        'my_pkg:1.2',
        False,
        InvalidPackageError('Invalid requirement string: my_pkg:1.2')
    ),
])
def test_requirement(req_str, is_path, err):
    if err is None:
        req = Requirement.from_string(req_str)
        assert isinstance(req.req_or_path, Path) is is_path
        assert req_str.strip().startswith('-e') is req.editable
        req2 = Requirement.from_string(str(req))
        assert req == req2
    else:
        with pytest.raises(type(err), match=re.escape(str(err))):
            _ = Requirement.from_string(req_str)
