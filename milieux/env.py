from dataclasses import dataclass
from datetime import datetime
import json
import os
from pathlib import Path
import shutil
from typing import Annotated, Optional

from loguru import logger
from typing_extensions import Doc

from milieux import PROG
from milieux.config import Config
from milieux.errors import EnvironmentExistsError, NoPackagesError, NoSuchEnvironmentError
from milieux.utils import run_command


@dataclass
class EnvManager:
    """Class for managing virtual environments."""
    config: Config

    def ensure_env_dir(self) -> None:
        """Checks if the environment directory exists, and if not, creates it."""
        if not (path := self.config.env_dir_path).exists():
            logger.info(f'mkdir -p {path}')
            path.mkdir(parents=True)

    def get_env_path(self, name: str) -> Path:
        """Gets the path to the environment with the given name.
        If no such environment exists, raises a NoSuchEnvironmentError."""
        env_path = self.config.env_dir_path / name
        if not env_path.exists():
            raise NoSuchEnvironmentError(name)
        return env_path

    def create(self,
        name: Annotated[str, Doc('name of environment')],
        packages: Annotated[Optional[list[str]], Doc('list of packages to install in the environment')] = None,
        force: Annotated[bool, Doc('force overwrite an existing environment')] = False
    ) -> None:
        """Creates a new environment
        Uses the version of Python currently on the user's PATH."""
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
        # TODO: use --seed to include pip/setuptools/wheel?
        res = run_command(cmd, capture_output=True)
        # TODO: packages (call `install`?)
        lines = [line for line in res.stderr.splitlines() if not line.startswith('Activate')]
        logger.info('\n'.join(lines))
        activate_path = new_env_dir / 'bin' / 'activate'
        logger.info(f'Activate with either of these commands:\n\tsource {activate_path}\n\t{PROG} env activate {name}')

    def install(self, name: str, packages: list[str]) -> None:
        """Installs one or more packages into the given environment."""
        if not packages:
            raise NoPackagesError('Must specify packages to install')
        cmd = ['uv', 'pip', 'install']
        if (index_url := self.config.pip.index_url):
            cmd.extend(['--index-url', index_url])
        # TODO: extra index URLs?
        cmd.extend(packages)
        env = {**os.environ, 'VIRTUAL_ENV': str(self.get_env_path(name))}
        run_command(cmd, env=env)

    def remove(self, name: str) -> None:
        """Deletes the environment with the given name."""
        env_path = self.get_env_path(name)
        logger.info(f'Deleting {name!r} environment')
        shutil.rmtree(env_path)
        logger.info(f'Deleted {env_path}')

    def show(self, name: Optional[str] = None) -> None:
        """Shows the existing environments.
        If name is provided, shows just the existing environment."""
        if name is None:
            env_dir = self.config.env_dir_path
            print(f'Environment directory: {env_dir}')
            envs = [p.name for p in env_dir.glob('*') if p.is_dir()]
            if envs:
                print('Environments:')
                print('\n'.join(f'    {p}' for p in envs))
            else:
                print('No environments exist.')
        else:
            path = self.get_env_path(name)
            created_at = datetime.fromtimestamp(path.stat().st_ctime).isoformat()
            d = {'name': name, 'path': str(path), 'created_at': created_at}
            print(json.dumps(d, indent=2))
