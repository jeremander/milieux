from dataclasses import dataclass, field
from typing import Any, Optional, Union

from fancy_dataclass.cli import CLIDataclass

from milieux.config import Config
from milieux.env import EnvManager


def _get_name_field(required: bool) -> Any:
    metadata = {'args': ['-n', '--name'], 'required': required, 'help': 'name of environment'}
    return field(default=None, metadata=metadata)

_packages_field_help = 'list of packages to install into the environment (can optionally include constraints, e.g. "numpy>=1.25")'


@dataclass
class _EnvSubcommand(CLIDataclass):

    def _run(self, manager: EnvManager) -> None:
        raise NotImplementedError

    def run(self) -> None:
        cfg = Config.get_config()
        assert cfg is not None, 'missing configurations'
        manager = EnvManager(config=cfg)
        self._run(manager)


@dataclass
class EnvSubcommand(_EnvSubcommand):
    """Base class for environment subcommands."""
    name: Optional[str] = _get_name_field(required=True)


@dataclass
class EnvActivate(EnvSubcommand, command_name='activate'):
    """Activate an environment."""
    name: Optional[str] = _get_name_field(required=True)

    def _run(self, manager: EnvManager) -> None:
        name = self.name or input('Name of environment: ')
        manager.activate(name)


@dataclass
class EnvCreate(EnvSubcommand, command_name='create'):
    """Create a new environment."""
    name: Optional[str] = _get_name_field(required=False)
    packages: list[str] = field(
        default_factory=list,
        metadata={'nargs': '+', 'help': _packages_field_help}
    )
    seed: bool = field(
        default=False,
        metadata={'help': 'install "seed" packages (e.g. `pip`) into environment'}
    )
    python: Optional[str] = field(
        default=None,
        metadata={'args': ['-p', '--python'], 'help': 'Python interpreter for the environment'}
    )
    force: bool = field(
        default=False,
        metadata={
            'args': ['-f', '--force'],
            'help': 'force overwrite of environment if it exists'
        }
    )

    def _run(self, manager: EnvManager) -> None:
        name = self.name or input('Name of environment: ')
        manager.create(name, packages=self.packages, seed=self.seed, python=self.python, force=self.force)


@dataclass
class EnvInstall(_EnvSubcommand, command_name='install'):
    """Install packages into an environment."""
    packages: list[str] = field(metadata={'help': _packages_field_help})
    name: Optional[str] = _get_name_field(required=True)
    requirements: list[str] = field(
        default_factory=list,
        metadata={'nargs': '+', 'args': ['-r', '--requirements'], 'help': 'requirements file(s) listing packages'}
    )
    distros: list[str] = field(
        default_factory=list,
        metadata={'nargs': '+', 'args': ['-d', '--distros'], 'help': 'distro name(s) providing packages'}
    )

    def _run(self, manager: EnvManager) -> None:
        assert self.name is not None
        # TODO: map distros to requirements files
        manager.install(self.name, packages=self.packages, requirements=self.requirements)


@dataclass
class EnvList(_EnvSubcommand, command_name='list'):
    """List all environments."""

    def _run(self, manager: EnvManager) -> None:
        manager.list()


@dataclass
class EnvRemove(EnvSubcommand, command_name='remove'):
    """Remove an environment."""

    def _run(self, manager: EnvManager) -> None:
        assert self.name is not None
        manager.remove(self.name)


@dataclass
class EnvShow(EnvSubcommand, command_name='show'):
    """Show info about an environment."""
    name: str = _get_name_field(required=True)

    def _run(self, manager: EnvManager) -> None:
        manager.show(self.name)


@dataclass
class EnvUninstall(_EnvSubcommand, command_name='uninstall'):
    """Install packages into an environment."""
    packages: list[str] = field(metadata={'help': _packages_field_help})
    name: Optional[str] = _get_name_field(required=True)
    requirements: list[str] = field(
        default_factory=list,
        metadata={'nargs': '+', 'args': ['-r', '--requirements'], 'help': 'requirements file(s) listing packages'}
    )
    distros: list[str] = field(
        default_factory=list,
        metadata={'nargs': '+', 'args': ['-d', '--distros'], 'help': 'distro name(s) providing packages'}
    )

    def _run(self, manager: EnvManager) -> None:
        assert self.name is not None
        # TODO: map distros to requirements files
        manager.uninstall(self.name, packages=self.packages, requirements=self.requirements)


@dataclass
class EnvCmd(CLIDataclass, command_name='env'):
    """Manage environments."""

    subcommand: Union[
        EnvActivate,
        EnvCreate,
        EnvInstall,
        EnvList,
        EnvRemove,
        EnvShow,
        EnvUninstall,
    ] = field(metadata={'subcommand': True})
