from __future__ import annotations

from pathlib import Path
import shlex
import subprocess
from typing import Any, Union

from rich.prompt import InvalidResponse, Prompt

from milieux import console, logger


AnyPath = Union[str, Path]


def run_command(cmd: list[Any], **kwargs: Any) -> subprocess.CompletedProcess[str]:
    """Runs a command (provided as a list) via subprocess.
    Passes any kwargs to subprocess.run."""
    cmd = [str(token) for token in cmd]
    logger.info(shlex.join(cmd))
    kwargs = {'text': True, **kwargs}  # use text mode by default
    return subprocess.run(cmd, **kwargs)


############
# FILE I/O #
############

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

def ensure_dir(path: Path) -> Path:
    """If the given directory does not exist, creates it.
    Then returns the Path."""
    if not path.exists():
        logger.info(f'mkdir -p {path}')
        path.mkdir(parents=True)
    if not path.is_dir():
        raise NotADirectoryError(path)
    return path

def read_lines(path: AnyPath) -> list[str]:
    """Reads lines of text from a file."""
    return Path(path).read_text().splitlines()


##########
# PROMPT #
##########

class NonemptyPrompt(Prompt):
    """Subclass of rich.prompt.Prompt requiring the input to be non-empty."""

    def process_response(self, value: str) -> str:  # noqa: D102
        if not value.strip():
            raise InvalidResponse(self.validate_error_message)
        return super().process_response(value)


########
# TEXT #
########

def eprint(s: str, **kwargs: Any) -> None:
    """Prints a string to stderr."""
    console.print(s, **kwargs)

PALETTE = {
    'distro': 'dark_orange3',
    'env': 'green4',
    'pkg': 'magenta',
}

def distro_sty(distro: str) -> str:
    """Styles a distro name."""
    color = PALETTE['distro']
    return f'[bold {color}]{distro}[/]'

def env_sty(env: str) -> str:
    """Styles an environment name."""
    color = PALETTE['env']
    return f'[bold {color}]{env}[/]'

def pkg_sty(pkg: str) -> str:
    """Styles a package name."""
    color = PALETTE['pkg']
    return f'[bold {color}]{pkg}[/]'
