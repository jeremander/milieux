from collections.abc import Sequence
from dataclasses import dataclass
from datetime import datetime
import json
import os
from pathlib import Path
import re
import shutil
from subprocess import CalledProcessError, CompletedProcess
from typing import Annotated, Any, Optional

from loguru import logger
from typing_extensions import Doc, Self

from milieux import PROG
from milieux.config import get_config
from milieux.distro import get_requirements
from milieux.errors import EnvError, EnvironmentExistsError, MilieuxError, NoPackagesError, NoSuchEnvironmentError
from milieux.utils import AnyPath, ensure_path, eprint, run_command


def get_env_base_dir() -> Path:
    """Checks if the configured environment directory exists, and if not, creates it."""
    cfg = get_config()
    return ensure_path(cfg.env_dir_path)


@dataclass
class Environment:
    """Class for interacting with a virtual environment."""
    name: Annotated[str, Doc('Name of environment')]
    dir_path: Annotated[Path, Doc('Path to environment directory')]

    def __init__(self, name: str, dir_path: Optional[Path] = None) -> None:
        self.name = name
        self.dir_path = dir_path or get_env_base_dir()

    @property
    def env_path(self) -> Path:
        """Gets the path to the environment.
        If no such environment exists, raises a NoSuchEnvironmentError."""
        env_path = self.dir_path / self.name
        if not env_path.exists():
            raise NoSuchEnvironmentError(self.name)
        return env_path

    @property
    def config_path(self) -> Path:
        """Gets the path to the environment config file."""
        return self.env_path / 'pyvenv.cfg'

    @property
    def bin_path(self) -> Path:
        """Gets the path to the environment's bin directory."""
        return self.env_path / 'bin'

    @property
    def activate_path(self) -> Path:
        """Gets the path to the environment's activation script."""
        return self.bin_path / 'activate'

    @property
    def python_version(self) -> str:
        """Gets the Python version for the environment."""
        with open(self.config_path) as f:
            s = f.read()
        match = re.search(r'version_info\s*=\s*(\d+\.\d+\.\d+)', s)
        if not match:
            raise MilieuxError(f'Could not get Python version info from {self.config_path}')
        (version,) = match.groups(0)
        assert isinstance(version, str)
        return version

    @property
    def site_packages_path(self) -> Path:
        """Gets the path to the environment's site_packages directory."""
        minor_version = '.'.join(self.python_version.split('.')[:2])
        return self.env_path / 'lib' / f'python{minor_version}' / 'site-packages'

    def run_command(self, cmd: list[str], **kwargs: Any) -> CompletedProcess[str]:
        """Runs a command with the VIRTUAL_ENV environment variable set."""
        cmd_env = {**os.environ, 'VIRTUAL_ENV': str(self.env_path)}
        return run_command(cmd, env=cmd_env, **kwargs)

    def get_installed_packages(self) -> list[str]:
        """Gets a list of installed packages in the environment."""
        cmd = ['uv', 'pip', 'freeze']
        res = self.run_command(cmd, text=True, capture_output=True)
        return res.stdout.splitlines()

    def get_info(self, list_packages: bool = False) -> dict[str, Any]:
        """Gets details about the environment, as a JSON-compatible dict."""
        path = self.env_path
        created_at = datetime.fromtimestamp(path.stat().st_ctime).isoformat()
        info: dict[str, Any] = {'name': self.name, 'path': str(path), 'created_at': created_at}
        if list_packages:
            info['packages'] = self.get_installed_packages()
        return info

    def _install_or_uninstall(self, install: bool, packages: Optional[list[str]] = None, requirements: Optional[Sequence[AnyPath]] = None, distros: Optional[list[str]] = None) -> None:
        """Installs one or more packages into the environment."""
        operation = 'install' if install else 'uninstall'
        reqs = get_requirements(requirements, distros)
        if (not packages) and (not requirements):
            raise NoPackagesError(f'Must specify packages to {operation}')
        cmd = ['uv', 'pip', operation]
        cfg = get_config()
        if install and (index_url := cfg.pip.index_url):
            cmd.extend(['--index-url', index_url])
        # TODO: extra index URLs?
        if packages:
            cmd.extend(packages)
        if requirements:
            cmd.extend(['-r'] + reqs)
        self.run_command(cmd)

    def activate(self) -> None:
        """Prints info about how to activate the environment."""
        activate_path = self.activate_path
        if not activate_path.exists():
            raise FileNotFoundError(activate_path)
        # NOTE: no easy way to activate new shell and "source" a file in Python
        # instead, we just print out the command
        print(f'source {activate_path}')
        eprint('\nTo activate the environment, run the following shell command:\n')
        eprint(f'source {activate_path}')
        eprint('\nAlternatively, you can run (with backticks):\n')
        eprint(f'`{PROG} env activate -n {self.name}`')
        eprint('\nTo deactivate the environment, run:\n')
        eprint('deactivate\n')

    @classmethod
    def new(cls,
        name: str,
        seed: bool = False,
        python: Optional[str] = None,
        force: bool = False,
    ) -> Self:
        """Creates a new environment.
        Uses the version of Python currently on the user's PATH."""
        env_base_dir = get_env_base_dir()
        new_env_dir = env_base_dir / name
        if new_env_dir.exists():
            msg = f'Environment {name!r} already exists'
            if force:
                logger.warning(f'{msg} -- overwriting')
                shutil.rmtree(new_env_dir)
            else:
                raise EnvironmentExistsError(msg)
        logger.info(f'Creating environment {name!r} in {new_env_dir}')
        new_env_dir.mkdir()
        cmd = ['uv', 'venv', new_env_dir]
        if seed:
            cmd.append('--seed')
        if python:
            cmd += ['--python', python]
        try:
            res = run_command(cmd, capture_output=True, check=True)
        except CalledProcessError as e:
            shutil.rmtree(new_env_dir)
            raise EnvError(e.stderr.rstrip()) from e
        lines = [line for line in res.stderr.splitlines() if not line.startswith('Activate')]
        logger.info('\n'.join(lines))
        env = cls(name, env_base_dir)
        logger.info(f'Activate with either of these commands:\n\tsource {env.activate_path}\n\t{PROG} env activate {name}')
        return env

    def freeze(self) -> None:
        """Prints out the packages currently installed in the environment."""
        packages = self.get_installed_packages()
        for pkg in packages:
            print(pkg)

    def install(self, packages: Optional[list[str]] = None, requirements: Optional[Sequence[AnyPath]] = None, distros: Optional[list[str]] = None) -> None:
        """Installs one or more packages into the environment."""
        _ = self.env_path  # ensure environment exists
        logger.info(f'Installing dependencies into {self.name!r} environment')
        self._install_or_uninstall(True, packages=packages, requirements=requirements, distros=distros)

    def remove(self) -> None:
        """Deletes the environment."""
        env_path = self.env_path
        logger.info(f'Deleting {self.name!r} environment')
        shutil.rmtree(env_path)
        logger.info(f'Deleted {env_path}')

    def show(self, list_packages: bool = False) -> None:
        """Shows details about the environment."""
        info = self.get_info(list_packages=list_packages)
        print(json.dumps(info, indent=2))

    def sync(self, requirements: Optional[Sequence[AnyPath]] = None, distros: Optional[list[str]] = None) -> None:
        """Syncs dependencies in a distro or requirements files to the environment.
        NOTE: unlike 'install', this ensures the environment exactly matches the dependencies afterward."""
        reqs = get_requirements(requirements, distros)
        if not reqs:
            raise NoPackagesError('Must specify dependencies to sync')
        logger.info(f'Syncing dependencies in {self.name!r} environment')
        cmd = ['uv', 'pip', 'sync'] + reqs
        self.run_command(cmd)

    def uninstall(self, packages: Optional[list[str]] = None, requirements: Optional[Sequence[AnyPath]] = None, distros: Optional[list[str]] = None) -> None:
        """Uninstalls one or more packages from the environment."""
        _ = self.env_path  # ensure environment exists
        logger.info(f'Uninstalling dependencies from {self.name!r} environment')
        self._install_or_uninstall(False, packages=packages, requirements=requirements, distros=distros)

    # NOTE: due to a bug in mypy (https://github.com/python/mypy/issues/15047), this method must come last
    @classmethod
    def list(cls) -> None:
        """Prints the list of existing environments."""
        env_base_dir = get_env_base_dir()
        print(f'Environment directory: {env_base_dir}')
        envs = [p.name for p in env_base_dir.glob('*') if p.is_dir()]
        if envs:
            print('Environments:')
            print('\n'.join(f'    {p}' for p in envs))
        else:
            print('No environments exist.')
