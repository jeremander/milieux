import importlib

import pytest

from milieux.doc import resolve_local_package_path, resolve_package_path, resolve_project_or_package_paths
from milieux.errors import PackageNotFoundError


EXAMPLE_PYPROJECT = """
[project]
name = "myproj"
"""

def _check_resolve_local_package_path(input_path, output_path):
    assert resolve_local_package_path(input_path) == output_path
    assert resolve_project_or_package_paths(str(input_path)) == [output_path]
    assert resolve_project_or_package_paths(f'-e {input_path}') == [output_path]

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
    pkg_path = resolve_package_path(pkg_name)
    mod = importlib.import_module(pkg_name)
    assert mod.__path__[0] == str(pkg_path)
    pkg_name = 'fake_package'
    with pytest.raises(ModuleNotFoundError, match=f"No module named '{pkg_name}'"):
        importlib.import_module(pkg_name)
    with pytest.raises(PackageNotFoundError, match='Package named .*fake_package.* was not found'):
        _ = resolve_package_path(pkg_name)
