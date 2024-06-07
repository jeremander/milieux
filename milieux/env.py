from dataclasses import dataclass
from datetime import datetime
import json
import os
from pathlib import Path
import re
import shutil
from subprocess import CalledProcessError
import sys
from typing import Annotated, Optional

from loguru import logger
from typing_extensions import Doc

from milieux import PROG
from milieux.config import Config
from milieux.errors import EnvError, EnvironmentExistsError, MilieuxError, NoPackagesError, NoSuchEnvironmentError
from milieux.utils import run_command


@dataclass
class Environment:
    """Class for interacting with a virtual environment."""
    dir_path: Annotated[Path, Doc('Path to environment directory')]
    name: Annotated[str, Doc('Name of environment')]

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
            raise MilieuxError(f'could not get Python version info from {self.config_path}')
        (version,) = match.groups(0)
        assert isinstance(version, str)
        return version

    @property
    def site_packages_path(self) -> Path:
        """Gets the path to the environment's site_packages directory."""
        minor_version = '.'.join(self.python_version.split('.')[:2])
        return self.env_path / 'lib' / f'python{minor_version}' / 'site-packages'


@dataclass
class EnvManager:
    """Class for managing virtual environments."""
    config: Config

    def ensure_env_dir(self) -> None:
        """Checks if the environment directory exists, and if not, creates it."""
        if not (path := self.config.env_dir_path).exists():
            logger.info(f'mkdir -p {path}')
            path.mkdir(parents=True)

    def get_environment(self, name: str) -> Environment:
        """Gets the Environment with the given name."""
        return Environment(self.config.env_dir_path, name)

    def activate(self, name: str) -> None:
        """Prints info about how to activate the environment."""
        env = self.get_environment(name)
        activate_path = env.activate_path
        if not activate_path.exists():
            raise FileNotFoundError(activate_path)
        # NOTE: no easy way to activate new shell and "source" a file in Python
        # instead, we just print out the command
        def eprint(s: str) -> None:
            print(s, file=sys.stderr)
        print(f'source {activate_path}')
        eprint('\nTo activate the environment, run the following shell command:\n')
        eprint(f'source {activate_path}')
        eprint('\nAlternatively, you can run (with backticks):\n')
        eprint(f'`{PROG} env activate -n {name}`')
        eprint('\nTo deactivate the environment, run:\n')
        eprint('deactivate\n')

    def create(self,
        name: str,
        packages: Optional[list[str]] = None,
        seed: bool = False,
        python: Optional[str] = None,
        force: bool = False,
    ) -> None:
        """Creates a new environment
        Uses the version of Python currently on the user's PATH."""
        if packages:
            raise NotImplementedError
        self.ensure_env_dir()
        new_env_dir = self.config.env_dir_path / name
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
        # TODO: packages (call `install`?)
        lines = [line for line in res.stderr.splitlines() if not line.startswith('Activate')]
        logger.info('\n'.join(lines))
        env = self.get_environment(name)
        logger.info(f'Activate with either of these commands:\n\tsource {env.activate_path}\n\t{PROG} env activate {name}')

    def _install_or_uninstall(self, install: bool, name: str, packages: Optional[list[str]] = None, requirements: Optional[list[str]] = None) -> None:
        """Installs one or more packages into the given environment."""
        operation = 'install' if install else 'uninstall'
        if (not packages) and (not requirements):
            raise NoPackagesError(f'Must specify packages to {operation}')
        cmd = ['uv', 'pip', operation]
        if install and (index_url := self.config.pip.index_url):
            cmd.extend(['--index-url', index_url])
        # TODO: extra index URLs?
        if packages:
            cmd.extend(packages)
        if requirements:
            cmd.extend(['-r'] + requirements)
        env = self.get_environment(name)
        cmd_env = {**os.environ, 'VIRTUAL_ENV': str(env.env_path)}
        run_command(cmd, env=cmd_env)

    def install(self, name: str, packages: Optional[list[str]] = None, requirements: Optional[list[str]] = None) -> None:
        """Installs one or more packages into the given environment."""
        self._install_or_uninstall(True, name, packages=packages, requirements=requirements)

    def remove(self, name: str) -> None:
        """Deletes the environment with the given name."""
        env_path = self.get_environment(name).env_path
        logger.info(f'Deleting {name!r} environment')
        shutil.rmtree(env_path)
        logger.info(f'Deleted {env_path}')

    def show(self, name: str) -> None:
        """Shows details about a particular environment."""
        path = self.get_environment(name).env_path
        created_at = datetime.fromtimestamp(path.stat().st_ctime).isoformat()
        d = {'name': name, 'path': str(path), 'created_at': created_at}
        # TODO: list of installed packages?
        print(json.dumps(d, indent=2))

    def uninstall(self, name: str, packages: Optional[list[str]] = None, requirements: Optional[list[str]] = None) -> None:
        """Uninstalls one or more packages from the given environment."""
        self._install_or_uninstall(False, name, packages=packages, requirements=requirements)

    # NOTE: due to a bug in mypy (https://github.com/python/mypy/issues/15047), this method must come last
    def list(self) -> None:
        """Prints the list of existing environments."""
        env_dir = self.config.env_dir_path
        print(f'Environment directory: {env_dir}')
        envs = [p.name for p in env_dir.glob('*') if p.is_dir()]
        if envs:
            print('Environments:')
            print('\n'.join(f'    {p}' for p in envs))
        else:
            print('No environments exist.')
