import importlib
from pathlib import Path
import re

import pytest

from milieux.errors import InvalidPackageError, PackageNotFoundError
from milieux.package import Requirement, _get_requirement_line, package_name_to_path, resolve_local_package_path


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


EXAMPLE_PYPROJECT = """
[project]
name = "myproj"
"""

def _check_resolve_local_package_path(input_path, output_path):
    assert resolve_local_package_path(input_path) == output_path
    assert Requirement.from_string(str(input_path)).get_package_paths() == [output_path]
    assert Requirement.from_string(f'-e {input_path}').get_package_paths() == [output_path]

def test_resolve_local_package_path(tmp_path):
    proj_dir = tmp_path / 'myproj'
    proj_dir.mkdir()
    pyproject_path = proj_dir / 'pyproject.toml'
    pyproject_path.write_text(EXAMPLE_PYPROJECT)
    with pytest.raises(FileNotFoundError, match='No package dir found'):
        _ = resolve_local_package_path(proj_dir)
    pkg_dir = proj_dir / 'myproj'
    pkg_dir.mkdir()
    _check_resolve_local_package_path(proj_dir, pkg_dir)
    pkg_dir.rmdir()
    pkg_dir = proj_dir / 'src' / 'myproj'
    pkg_dir.mkdir(parents=True)
    _check_resolve_local_package_path(proj_dir, pkg_dir)
    pkg_dir.rmdir()
    some_dir = proj_dir / 'some_dir'
    some_dir.mkdir()
    (some_dir / '__init__.py').touch()
    _check_resolve_local_package_path(proj_dir, some_dir)
    pyproject_path.unlink()
    _check_resolve_local_package_path(proj_dir, some_dir)

def test_resolve_installed_package_path(tmp_path):
    # one of the dependencies is guaranteed to be installed
    pkg_name = 'hatch'
    pkg_path = package_name_to_path(pkg_name)
    mod = importlib.import_module(pkg_name)
    assert mod.__path__[0] == str(pkg_path)
    pkg_name = 'fake_package'
    with pytest.raises(ModuleNotFoundError, match=f"No module named '{pkg_name}'"):
        importlib.import_module(pkg_name)
    with pytest.raises(PackageNotFoundError, match='Package named .*fake_package.* was not found'):
        _ = package_name_to_path(pkg_name)
