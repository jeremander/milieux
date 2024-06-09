from __future__ import annotations

from pathlib import Path
import shlex
import subprocess
import sys
from typing import Any, Union

from loguru import logger


AnyPath = Union[str, Path]


def run_command(cmd: list[Any], **kwargs: Any) -> subprocess.CompletedProcess[str]:
    """Runs a command (provided as a list) via subprocess.
    Passes any kwargs to subprocess.run."""
    cmd = [str(token) for token in cmd]
    logger.info(shlex.join(cmd))
    kwargs = {'text': True, **kwargs}  # use text mode by default
    return subprocess.run(cmd, **kwargs)

def resolve_path(path: str, base_dir: Path) -> Path:
    """Attempts to resolve a path to an absolute path.
    If it is a relative path, resolves it relative to the given base_dir."""
    p = Path(path)
    first_part = p.parts[0] if p.parts else None
    if p.is_absolute() or (first_part == '.'):
        if p.exists():
            return p
        raise FileNotFoundError(path)
    if first_part == '..':
        return base_dir.parent / '/'.join(p.parts[1:])
    # otherwise, a relative path
    return base_dir / path

def ensure_path(path: Path) -> Path:
    """If the given path does not exist, creates it.
    Then returns the Path."""
    if not path.exists():
        logger.info(f'mkdir -p {path}')
        path.mkdir(parents=True)
    return path

def read_lines(path: AnyPath) -> list[str]:
    """Reads lines of text from a file."""
    return Path(path).read_text().splitlines()

def eprint(s: str, **kwargs: Any) -> None:
    """Prints a string to stderr."""
    print(s, file=sys.stderr, **kwargs)
