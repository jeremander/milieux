from __future__ import annotations

from pathlib import Path
import shlex
import subprocess
from typing import Any

from loguru import logger


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
        return resolve_path(str(p.resolve()), base_dir)
    # otherwise, a relative path
    return base_dir / path
