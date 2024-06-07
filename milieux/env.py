from dataclasses import dataclass
from datetime import datetime
import json
import os
from pathlib import Path
import shutil
from subprocess import CalledProcessError
import sys
from typing import Optional

from loguru import logger

from milieux import PROG
from milieux.config import Config
from milieux.errors import EnvError, EnvironmentExistsError, NoPackagesError, NoSuchEnvironmentError
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

    def get_activate_path(self, name: str) -> Path:
        """Given an environment name, gets the path to the environment's activation script."""
        return self.get_env_path(name) / 'bin' / 'activate'

    def activate(self, name: str) -> None:
        """Activates an environment."""
        activate_path = self.get_activate_path(name)
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
        activate_path = self.get_activate_path(name)
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

    def remove(self, name: str) -> None:
        """Deletes the environment with the given name."""
        env_path = self.get_env_path(name)
        logger.info(f'Deleting {name!r} environment')
        shutil.rmtree(env_path)
        logger.info(f'Deleted {env_path}')

    def show(self, name: str) -> None:
        """Shows details about a particular environment."""
        path = self.get_env_path(name)
        created_at = datetime.fromtimestamp(path.stat().st_ctime).isoformat()
        d = {'name': name, 'path': str(path), 'created_at': created_at}
        print(json.dumps(d, indent=2))
