"""Helper functions related to resolving package names and paths."""

from dataclasses import dataclass
from functools import total_ordering
from pathlib import Path
from typing import Optional

import packaging.requirements
from packaging.requirements import InvalidRequirement, ParserSyntaxError  # type: ignore[attr-defined]
from typing_extensions import Self

from milieux.errors import InvalidPackageError, NoSuchRequirementsFileError
from milieux.utils import AnyPath, read_lines


@dataclass(frozen=True)
@total_ordering
class Requirement:
    """Class representing a line in a requirements.txt file."""
    req_or_path: packaging.requirements.Requirement | Path
    editable: bool = False

    def __str__(self) -> str:
        parts = [
            '-e ' if self.editable else '',
            'file://' if isinstance(self.req_or_path, Path) else '',
            str(self.req_or_path),
        ]
        return ''.join(parts)

    def __lt__(self, other: Self) -> bool:
        return (str(self.req_or_path), not self.editable) < (str(other.req_or_path), not other.editable)

    @classmethod
    def from_string(cls, req_str: str) -> Self:
        """Parses a requirement string to a Requirement object."""
        toks = req_str.split()
        editable = bool(toks) and (toks[0] == '-e')
        toks = [tok for tok in toks if not tok.startswith('-')]
        req_str = ' '.join(toks)
        if ('/' in req_str) or req_str.startswith('.'):  # assume a path
            req_str = req_str.strip().removeprefix('file://')
            req: packaging.requirements.Requirement | Path = Path(req_str)
        else:
            try:
                req = packaging.requirements.Requirement(req_str)
            except (InvalidRequirement, ParserSyntaxError) as e:
                raise InvalidPackageError(f'Invalid requirement string: {req_str}') from e
        return cls(req, editable)


def get_requirement_name(req_str: str) -> str:
    """Gets a requirement name from a requirement string.
    E.g. "pkg_name>=2.7" resolves to "pkg_name"."""
    toks = [tok for tok in req_str.split() if not tok.startswith('-')]
    req_str = ' '.join(toks)
    try:
        return packaging.requirements.Requirement(req_str).name
    except (InvalidRequirement, ParserSyntaxError) as e:
        raise InvalidPackageError(req_str) from e

def _get_requirement_line(line: str) -> Optional[str]:
    """Given a line in a requirements file, returns a requirement string if the line is nontrivial, stripping off any '#' comments."""
    line = line.split('#', maxsplit=1)[0].strip()
    return line or None

def get_requirements_from_file(req_path: AnyPath) -> list[Requirement]:
    """Given a path to a requirements file, returns a list of Requirement objects."""
    try:
        lines = read_lines(req_path)
    except (FileNotFoundError, IsADirectoryError) as e:
        raise NoSuchRequirementsFileError(str(req_path)) from e
    return [Requirement.from_string(req_str) for line in lines if (req_str := _get_requirement_line(line))]
