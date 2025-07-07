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

import jinja2
from typing_extensions import Doc, Self

from milieux import PROG, logger
from milieux.config import get_config
from milieux.distro import get_requirements
from milieux.errors import EnvError, EnvironmentExistsError, MilieuxError, NoPackagesError, NoSuchEnvironmentError, TemplateError
from milieux.utils import AnyPath, ensure_dir, env_sty, eprint, run_command


def get_env_base_dir() -> Path:
    """Checks if the configured environment directory exists, and if not, creates it."""
    cfg = get_config()
    return ensure_dir(cfg.env_dir_path)

# defines the available environment variables for jinja templates
TEMPLATE_ENV_VARS = {
    'ENV_NAME': 'environment name',
    'ENV_DIR': 'environment directory',
    'ENV_BASE_DIR': 'base directory for all environments',
    'ENV_CONFIG_PATH': 'path to environment config file',
    'ENV_BIN_DIR': 'environment bin directory',
    'ENV_LIB_DIR': 'environment lib directory',
    'ENV_SITE_PACKAGES_DIR': 'environment site_packages directory',
    'ENV_ACTIVATE_PATH': 'path to environment activation script',
    'ENV_PYVERSION': 'Python version for the environment (e.g. 3.11.2)',
    'ENV_PYVERSION_MINOR': 'Minor Python version for the environment (e.g. 3.11)',
}


@dataclass
class Environment:
    """Class for interacting with a virtual environment."""
    name: Annotated[str, Doc('Name of environment')]
    dir_path: Annotated[Path, Doc('Path to environment directory')]

    def __init__(self, name: str, dir_path: Optional[Path] = None) -> None:
        if name.startswith('.'):
            raise NoSuchEnvironmentError(name)
        self.name = name
        self.dir_path = dir_path or get_env_base_dir()

    @property
    def env_dir(self) -> Path:
        """Gets the path to the environment.
        If no such environment exists, raises a NoSuchEnvironmentError."""
        env_dir = self.dir_path / self.name
        if not env_dir.is_dir():
            raise NoSuchEnvironmentError(self.name)
        return env_dir

    @property
    def config_path(self) -> Path:
        """Gets the path to the environment config file."""
        return self.env_dir / 'pyvenv.cfg'

    @property
    def bin_dir(self) -> Path:
        """Gets the path to the environment's bin directory."""
        return self.env_dir / 'bin'

    @property
    def lib_dir(self) -> Path:
        """Gets the path to the environment's lib directory."""
        return self.env_dir / 'lib'

    @property
    def site_packages_dir(self) -> Path:
        """Gets the path to the environment's site_packages directory."""
        minor_version = '.'.join(self.python_version.split('.')[:2])
        return self.env_dir / 'lib' / f'python{minor_version}' / 'site-packages'

    @property
    def activate_path(self) -> Path:
        """Gets the path to the environment's activation script."""
        return self.bin_dir / 'activate'

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
    def template_env_vars(self) -> dict[str, Any]:
        """Gets a mapping from template environment variables to their values for this environment.
        NOTE: the values may be strings or Path objects (the latter make it easier to perform path operations within a jinja template)."""
        pyversion = self.python_version
        pyversion_minor = '.'.join(pyversion.split('.')[:2])
        env_vars = {
            'ENV_NAME': self.name,
            'ENV_DIR': self.env_dir,
            'ENV_BASE_DIR': self.dir_path,
            'ENV_CONFIG_PATH': self.config_path,
            'ENV_BIN_DIR': self.bin_dir,
            'ENV_LIB_DIR': self.lib_dir,
            'ENV_SITE_PACKAGES_DIR': self.site_packages_dir,
            'ENV_ACTIVATE_PATH': self.activate_path,
            'ENV_PYVERSION': pyversion,
            'ENV_PYVERSION_MINOR': pyversion_minor,
        }
        assert set(env_vars) == set(TEMPLATE_ENV_VARS)
        return env_vars

    def run_command(self, cmd: list[str], **kwargs: Any) -> CompletedProcess[str]:
        """Runs a command with the VIRTUAL_ENV environment variable set."""
        cmd_env = {**os.environ, 'VIRTUAL_ENV': str(self.env_dir)}
        return run_command(cmd, env=cmd_env, check=True, **kwargs)

    def get_installed_packages(self) -> list[str]:
        """Gets a list of installed packages in the environment."""
        cmd = ['uv', 'pip', 'freeze']
        res = self.run_command(cmd, text=True, capture_output=True)
        return res.stdout.splitlines()

    def get_info(self, list_packages: bool = False) -> dict[str, Any]:
        """Gets details about the environment, as a JSON-compatible dict."""
        path = self.env_dir
        created_at = datetime.fromtimestamp(path.stat().st_ctime).isoformat()
        info: dict[str, Any] = {'name': self.name, 'path': str(path), 'created_at': created_at}
        if list_packages:
            info['packages'] = self.get_installed_packages()
        return info

    def _install_or_uninstall_cmd(
        self,
        install: bool,
        packages: Optional[list[str]] = None,
        requirements: Optional[Sequence[AnyPath]] = None,
        distros: Optional[list[str]] = None,
        editable: Optional[str] = None,
    ) -> list[str]:
        """Installs one or more packages into the environment."""
        operation = 'install' if install else 'uninstall'
        reqs = get_requirements(requirements, distros)
        if (not editable) and (not packages) and (not reqs):
            raise NoPackagesError(f'Must specify packages to {operation}')
        cmd = ['uv', 'pip', operation]
        if install:
            cmd.extend(get_config().pip.uv_args)
        # TODO: extra index URLs?
        if packages:
            cmd.extend(packages)
        if reqs:
            cmd.extend(['-r'] + reqs)
        return cmd

    def activate(self) -> None:
        """Prints info about how to activate the environment."""
        activate_path = self.activate_path
        if not activate_path.exists():
            raise FileNotFoundError(activate_path)
        # NOTE: no easy way to activate new shell and "source" a file in Python
        # instead, we just print out the command
        print(f'source {activate_path}')
        eprint('\nTo activate the environment, run the following shell command:\n')
        eprint(f'source {activate_path}', highlight=False)
        eprint('\nAlternatively, you can run (with backticks):\n', highlight=False)
        eprint(f'`{PROG} env activate {self.name}`')
        eprint('\nTo deactivate the environment, run:\n')
        eprint('deactivate\n')

    @classmethod
    def new(
        cls,
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
            msg = f'Environment {env_sty(name)} already exists'
            if force:
                logger.warning(f'{msg} -- overwriting')
                shutil.rmtree(new_env_dir)
            else:
                raise EnvironmentExistsError(msg)
        logger.info(f'Creating environment {env_sty(name)} in {new_env_dir}')
        new_env_dir.mkdir()
        cmd = ['uv', 'venv', str(new_env_dir)] + get_config().pip.uv_args
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
        eprint('\n'.join(lines), highlight=False)
        env = cls(name, env_base_dir)
        logger.info(f'Activate with either of these commands:\n\tsource {env.activate_path}\n\t{PROG} env activate {name}', extra={'highlighter': None})
        return env

    def freeze(self) -> None:
        """Prints out the packages currently installed in the environment."""
        packages = self.get_installed_packages()
        for pkg in packages:
            print(pkg)

    def install(
        self,
        packages: Optional[list[str]] = None,
        requirements: Optional[Sequence[AnyPath]] = None,
        distros: Optional[list[str]] = None,
        upgrade: bool = False,
        editable: Optional[str] = None,
    ) -> None:
        """Installs one or more packages into the environment."""
        _ = self.env_dir  # ensure environment exists
        logger.info(f'Installing dependencies into {env_sty(self.name)} environment')
        cmd = self._install_or_uninstall_cmd(True, packages=packages, requirements=requirements, distros=distros, editable=editable)
        if upgrade:
            cmd.append('--upgrade')
        if editable:
            cmd += ['--editable', editable]
        self.run_command(cmd)

    def remove(self) -> None:
        """Deletes the environment."""
        env_dir = self.env_dir
        logger.info(f'Deleting {env_sty(self.name)} environment')
        shutil.rmtree(env_dir)
        logger.info(f'Deleted {env_dir}')

    def render_template(self, template: Path, suffix: Optional[str] = None, extra_vars: Optional[dict[str, Any]] = None) -> None:
        """Renders a jinja template, filling in variables from the environment.
        If suffix is None, prints the output to stdout.
        Otherwise, saves a new file with the original file extension replaced by this suffix.
        extra_vars is an optional mapping from extra variables to values."""
        # error if unknown variables are present
        env = jinja2.Environment(undefined=jinja2.StrictUndefined)
        try:
            input_template = env.from_string(template.read_text())
            kwargs = {**self.template_env_vars, **(extra_vars or {})}
            output = input_template.render(**kwargs)
        except jinja2.exceptions.TemplateError as e:
            msg = f'Error rendering template {template} - {e}'
            raise TemplateError(msg) from e
        if suffix is None:
            print(output)
        else:
            suffix = suffix if suffix.startswith('.') else ('.' + suffix)
            output_path = template.with_suffix(suffix)
            output_path.write_text(output)
            logger.info(f'Rendered template {template} to {output_path}')

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
        logger.info(f'Syncing dependencies in {env_sty(self.name)} environment')
        cmd = ['uv', 'pip', 'sync'] + reqs + get_config().pip.uv_args
        self.run_command(cmd)

    def uninstall(
        self,
        packages: Optional[list[str]] = None,
        requirements: Optional[Sequence[AnyPath]] = None,
        distros: Optional[list[str]] = None
    ) -> None:
        """Uninstalls one or more packages from the environment."""
        _ = self.env_dir  # ensure environment exists
        logger.info(f'Uninstalling dependencies from {env_sty(self.name)} environment')
        cmd = self._install_or_uninstall_cmd(False, packages=packages, requirements=requirements, distros=distros)
        self.run_command(cmd)

    # NOTE: due to a bug in mypy (https://github.com/python/mypy/issues/15047), this method must come last
    @classmethod
    def list(cls) -> None:
        """Prints the list of existing environments."""
        env_base_dir = get_env_base_dir()
        eprint(f'Environment directory: {env_base_dir}')
        envs = sorted([p.name for p in env_base_dir.glob('*') if p.is_dir()])
        if envs:
            eprint('──────────────\n [bold]Environments[/]\n──────────────')
            for env in envs:
                print(env)
        else:
            eprint('No environments exist.')


def get_active_environment() -> Optional[Environment]:
    """Gets an Environment for the current active environment, provided that one is active and is a subdirectory of the configured environment directory.
    Returns None otherwise."""
    if (virtual_env := os.environ.get('VIRTUAL_ENV')) is None:
        return None
    base_dir = get_env_base_dir()
    venv_path = Path(virtual_env)
    venv_name = venv_path.name
    if venv_path == (base_dir / venv_name):
        return Environment(venv_name)
    return None
