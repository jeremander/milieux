import pytest

from milieux.doc import resolve_local_package_path


EXAMPLE_PYPROJECT = """
[project]
name = "myproj"
"""

def test_resolve_local_package_path(tmp_path):
    proj_dir = tmp_path / 'myproj'
    proj_dir.mkdir()
    pyproject_path = proj_dir / 'pyproject.toml'
    pyproject_path.write_text(EXAMPLE_PYPROJECT)
    with pytest.raises(FileNotFoundError, match='No package dir found'):
        _ = resolve_local_package_path(proj_dir)
    pkg_dir = proj_dir / 'myproj'
    pkg_dir.mkdir()
    assert resolve_local_package_path(proj_dir) == pkg_dir
    pkg_dir.rmdir()
    pkg_dir = proj_dir / 'src' / 'myproj'
    pkg_dir.mkdir(parents=True)
    assert resolve_local_package_path(proj_dir) == pkg_dir
    pkg_dir.rmdir()
    some_dir = proj_dir / 'some_dir'
    some_dir.mkdir()
    (some_dir / '__init__.py').touch()
    assert resolve_local_package_path(proj_dir) == some_dir
    pyproject_path.unlink()
    assert resolve_local_package_path(proj_dir) == some_dir
