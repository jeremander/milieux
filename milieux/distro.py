from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path
from subprocess import CalledProcessError
from typing import Annotated, Optional

from typing_extensions import Doc, Self

from milieux import logger
from milieux.config import get_config
from milieux.errors import DistroExistsError, InvalidDistroError, NoPackagesError, NoSuchDistroError, NoSuchRequirementsFileError
from milieux.utils import AnyPath, distro_sty, ensure_dir, eprint, read_lines, run_command


def get_distro_base_dir() -> Path:
    """Checks if the configured distro directory exists, and if not, creates it."""
    cfg = get_config()
    return ensure_dir(cfg.distro_dir_path)

def get_requirements(requirements: Optional[Sequence[AnyPath]] = None, distros: Optional[Sequence[str]] = None) -> list[str]:
    """Helper function to get requirements files, given a list of requirements files and/or distro names."""
    reqs = [str(req) for req in requirements] if requirements else []
    if distros:  # get requirements path from distro name
        reqs += [str(Distro(name).path) for name in distros]
    return reqs

def get_packages(packages: Optional[Sequence[str]] = None, requirements: Optional[Sequence[AnyPath]] = None, distros: Optional[Sequence[str]] = None) -> list[str]:
    """Given a list of packages and a list of requirements files, gets a list of all packages therein.
    Deduplicates any identical entries, and sorts alphabetically."""
    reqs = get_requirements(requirements, distros)
    if (not packages) and (not reqs):
        raise NoPackagesError('Must specify at least one package')
    pkgs: set[str] = set()
    if packages:
        pkgs.update(packages)
    if reqs:
        for req in reqs:
            try:
                pkgs.update(stripped for line in read_lines(req) if (stripped := line.strip()))
            except (FileNotFoundError, IsADirectoryError) as e:
                raise NoSuchRequirementsFileError(str(req)) from e
    return sorted(pkgs)


@dataclass
class Distro:
    """Class for interacting with a distro (set of Python package requirements)."""
    name: Annotated[str, Doc('Name of distro')]
    dir_path: Annotated[Path, Doc('Path to distro directory')]

    def __init__(self, name: str, dir_path: Optional[Path] = None) -> None:
        self.name = name
        self.dir_path = dir_path or get_distro_base_dir()
        self._path = self.dir_path / f'{name}.txt'

    def exists(self) -> bool:
        """Returns True if the distro exists."""
        return self._path.exists()

    @property
    def path(self) -> Path:
        """Gets the path to the distro (requirements file).
        If no such file exists, raises a NoSuchDistroError."""
        if not self.exists():
            raise NoSuchDistroError(self.name)
        return self._path

    def get_packages(self) -> list[str]:
        """Gets the list of packages in the distro."""
        packages = []
        for line in read_lines(self.path):
            line = line.strip()
            if not line.startswith('#'):  # skip comments
                packages.append(line)
        return packages

    def lock(self, annotate: bool = False) -> str:
        """Locks the packages in a distro to their pinned versions.
        Returns the output as a string."""
        logger.info(f'Locking dependencies for {distro_sty(self.name)} distro')
        cmd = ['uv', 'pip', 'compile', str(self.path)]
        cmd.extend(get_config().pip.uv_args)
        if not annotate:
            cmd.append('--no-annotate')
        try:
            return run_command(cmd, check=True, text=True, capture_output=True).stdout
        except CalledProcessError as e:
            raise InvalidDistroError('\n' + e.stderr) from e

    @classmethod
    def new(cls,
        name: str,
        packages: Optional[list[str]] = None,
        requirements: Optional[Sequence[AnyPath]] = None,
        distros: Optional[list[str]] = None,
        force: bool = False
    ) -> Self:
        """Creates a new distro."""
        packages = get_packages(packages, requirements, distros)
        distro_base_dir = get_distro_base_dir()
        distro_path = distro_base_dir / f'{name}.txt'
        if distro_path.exists():
            msg = f'Distro {distro_sty(name)} already exists'
            if force:
                logger.warning(f'{msg} -- overwriting')
                distro_path.unlink()
            else:
                raise DistroExistsError(msg)
        logger.info(f'Creating distro {distro_sty(name)}')
        with open(distro_path, 'w') as f:
            for pkg in packages:
                print(pkg, file=f)
        logger.info(f'Wrote {distro_sty(name)} requirements to {distro_path}')
        return cls(name, distro_base_dir)

    def remove(self) -> None:
        """Deletes the distro."""
        path = self.path
        logger.info(f'Deleting {distro_sty(self.name)} distro')
        path.unlink()
        logger.info(f'Deleted {path}')

    def show(self) -> None:
        """Prints out the packages in the distro."""
        eprint(f'Distro {distro_sty(self.name)} is located at: {self.path}')
        eprint('──────────\n [bold]Packages[/]\n──────────')
        for pkg in self.get_packages():
            print(pkg)

    # NOTE: due to a bug in mypy (https://github.com/python/mypy/issues/15047), this method must come last
    @classmethod
    def list(cls) -> None:
        """Prints the list of existing distros."""
        distro_base_dir = get_distro_base_dir()
        eprint(f'Distro directory: {distro_base_dir}')
        distros = sorted([p.stem for p in distro_base_dir.glob('*.txt') if p.is_file()])
        if distros:
            eprint('─────────\n [bold]Distros[/]\n─────────')
            for distro in distros:
                print(distro)
        else:
            eprint('No distros exist.')
