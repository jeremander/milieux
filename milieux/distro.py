from dataclasses import dataclass
from pathlib import Path
from typing import Annotated, Optional

from loguru import logger
from typing_extensions import Doc, Self

from milieux.config import get_config
from milieux.errors import DistroExistsError, NoPackagesError, NoSuchDistributionError, NoSuchRequirementsFileError
from milieux.utils import ensure_path, read_lines


def get_distro_base_dir() -> Path:
    """Checks if the configured distro directory exists, and if not, creates it."""
    cfg = get_config()
    return ensure_path(cfg.distro_dir_path)

def get_packages(packages: Optional[list[str]] = None, requirements: Optional[list[Path]] = None) -> list[str]:
    """Given a list of packages and a list of requirements files, gets a list of all packages therein.
    Deduplicates any identical entries, and sorts alphabetically."""
    if (not packages) and (not requirements):
        raise NoPackagesError('Must specify at least one package')
    pkgs = set()
    if packages:
        pkgs.update(packages)
    if requirements:
        for req in requirements:
            try:
                pkgs.update(stripped for line in read_lines(req) if (stripped := line.strip()))
            except FileNotFoundError as e:
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

    @property
    def path(self) -> Path:
        """Gets the path to the distro (requirements file).
        If no such file exists, raises a NoSuchDistributionError."""
        distro_path = self.dir_path / f'{self.name}.in'
        if not distro_path.exists():
            raise NoSuchDistributionError(self.name)
        return distro_path

    @classmethod
    def new(cls,
        name: str,
        packages: Optional[list[str]] = None,
        requirements: Optional[list[Path]] = None,
        force: bool = False
    ) -> Self:
        """Creates a new distro."""
        packages = get_packages(packages, requirements)
        distro_base_dir = get_distro_base_dir()
        distro_path = distro_base_dir / f'{name}.in'
        if distro_path.exists():
            msg = f'Distro {name!r} already exists'
            if force:
                logger.warning(f'{msg} -- overwriting')
                distro_path.unlink()
            else:
                raise DistroExistsError(msg)
        with open(distro_path, 'w') as f:
            for pkg in packages:
                print(pkg, file=f)
        logger.info(f'Wrote {name!r} requirements to {distro_path}')
        return cls(name, distro_base_dir)

    # NOTE: due to a bug in mypy (https://github.com/python/mypy/issues/15047), this method must come last
    @classmethod
    def list(cls) -> None:
        """Prints the list of existing distros."""
        distro_base_dir = get_distro_base_dir()
        print(f'Distro directory: {distro_base_dir}')
        distros = [p.stem for p in distro_base_dir.glob('*') if p.is_dir()]
        if distros:
            print('Distros:')
            print('\n'.join(f'    {p}' for p in distros))
        else:
            print('No distros exist.')
