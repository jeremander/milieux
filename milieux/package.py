"""Helper functions related to resolving package names and paths."""

from dataclasses import dataclass
from functools import total_ordering
import importlib
from pathlib import Path
from typing import Optional

import packaging.requirements
from packaging.requirements import InvalidRequirement, ParserSyntaxError  # type: ignore[attr-defined]
import tomli  # TODO: use tomllib once minimum Python 3.11 is supported
from typing_extensions import Self

from milieux.errors import InvalidPackageError, NoSuchRequirementsFileError, PackageNotFoundError
from milieux.utils import AnyPath, read_lines


def resolve_local_package_path(path: Path) -> Path:
    """Given a path to a local Python project, resolves the top-level package path."""
    root = Path(path).resolve()
    pyproject_path = root / 'pyproject.toml'
    if pyproject_path.exists():
        with pyproject_path.open('rb') as f:
            data = tomli.load(f)
        # try PEP 621 first
        if (name := data.get('project', {}).get('name')):
            name = name.replace('-', '_')
            # infer package dir from name
            p: Path = root / name
            if p.is_dir():
                return p
            # next, try src subdirectory
            src_dir = root / 'src'
            if src_dir.is_dir():
                p = src_dir / name
                if p.is_dir():
                    return p
    # fallback: look for any subdir with __init__.py
    for child in root.iterdir():
        if child.name.startswith('test'):
            continue
        if (child / '__init__.py').exists():
            return child
    raise FileNotFoundError(f'No package dir found in {path}')

def get_package_names_from_project(proj_name: str) -> list[str]:
    """Resolves a Python project ("distribution") name to one or more package names."""
    try:
        dist = importlib.metadata.distribution(proj_name)
    except importlib.metadata.PackageNotFoundError as e:
        raise PackageNotFoundError(proj_name) from e
    # assume packages are top-level directories containing __init__.py
    # XXX: is this robust enough?
    package_names = []
    for p in (dist.files or []):
        if (len(p.parts) == 2) and (p.parts[1] == '__init__.py'):
            package_names.append(p.parts[0])
    return package_names

def package_name_to_path(pkg_name: str) -> Path:
    """Resolves a package or module name to an absolute path."""
    try:
        mod = importlib.import_module(pkg_name)
    except ModuleNotFoundError as e:
        raise PackageNotFoundError(pkg_name) from e
    if mod.__file__ is None:
        raise PackageNotFoundError(pkg_name)
    path = Path(mod.__file__)
    if path.name ==  '__init__.py':
        path = path.parent
    return path


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

    def get_package_paths(self) -> list[Path]:
        """Resolves the package or project name to a list of absolute paths of packages."""
        if isinstance(self.req_or_path, Path):
            if (path := self.req_or_path).exists():
                # if path is to a project (containing a pyrpoject.toml), find the top-level package directory
                try:
                    return [resolve_local_package_path(path)]
                except FileNotFoundError as e:
                    raise PackageNotFoundError(str(path)) from e
            raise PackageNotFoundError(str(path))
        # otherwise, see if the name is a package
        name = self.req_or_path.name
        try:
            path = package_name_to_path(name)
            return [path]
        except PackageNotFoundError:
            # try interpreting as a project instead of a package
            pkg_names = get_package_names_from_project(name)
            return [package_name_to_path(pkg_name) for pkg_name in pkg_names]


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
