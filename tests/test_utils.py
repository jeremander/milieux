from pathlib import Path

import pytest

from milieux.utils import resolve_path


def test_resolve_path(tmpdir):
    assert resolve_path('.', tmpdir) == tmpdir
    p = Path(tmpdir / 'file.txt')
    assert resolve_path('file.txt', tmpdir) == p
    assert resolve_path('./file.txt', tmpdir) == p
    with pytest.raises(FileNotFoundError, match='file.txt'):
        _ = resolve_path(str(p), tmpdir)
    p.touch()
    assert resolve_path(str(p), tmpdir) == p
    subdir = Path(tmpdir / 'subdir')
    assert resolve_path('..', subdir) == tmpdir
    assert resolve_path('../file.txt', subdir) == p
