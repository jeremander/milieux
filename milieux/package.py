"""Helper functions related to resolving package names and paths."""

from typing import Optional

from packaging.requirements import InvalidRequirement, ParserSyntaxError, Requirement  # type: ignore[attr-defined]

from milieux.errors import InvalidPackageError, NoSuchRequirementsFileError
from milieux.utils import AnyPath, read_lines


def get_requirement_name(req_str: str) -> str:
    """Gets a requirement name from a requirement string.
    E.g. "pkg_name>=2.7" resolves to "pkg_name"."""
    toks = [tok for tok in req_str.split() if not tok.startswith('-')]
    req_str = ' '.join(toks)
    try:
        return Requirement(req_str).name
    except (InvalidRequirement, ParserSyntaxError) as e:
        raise InvalidPackageError(req_str) from e

def _parse_package_from_requirements(line: str) -> Optional[str]:
    """Given a line in a requirements file, returns a package name if the line is nontrivial, stripping off any '#' comments."""
    line = line.split('#', maxsplit=1)[0].strip()
    return line or None

def get_packages_from_requirements(requirements: AnyPath) -> list[str]:
    """Given a requirements file, returns a list of packages found therein."""
    try:
        lines = read_lines(requirements)
    except (FileNotFoundError, IsADirectoryError) as e:
        raise NoSuchRequirementsFileError(str(requirements)) from e
    return [pkg for line in lines if (pkg := _parse_package_from_requirements(line))]
