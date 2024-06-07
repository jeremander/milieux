from dataclasses import dataclass, field
from typing import Any, Optional, Union

from fancy_dataclass.cli import CLIDataclass

from milieux.config import Config
from milieux.env import EnvManager


def _get_name_field(required: bool) -> Any:
    metadata = {'args': ['-n', '--name'], 'required': required, 'help': 'name of environment'}
    return field(default=None, metadata=metadata)

def _get_packages_field() -> Any:
    metadata = {
        'nargs': '+',
        'help': 'list of packages to install into the environment (can optionally include constraints, e.g. "numpy>=1.25")'
    }
    return field(default_factory=list, metadata=metadata)


@dataclass
class EnvSubcommand(CLIDataclass):
    """Base class for environment subcommands."""
    name: Optional[str] = _get_name_field(required=True)

    def _run(self, manager: EnvManager) -> None:
        raise NotImplementedError

    def run(self) -> None:  # noqa: D102
        cfg = Config.get_config()
        assert cfg is not None, 'missing configurations'
        manager = EnvManager(config=cfg)
        self._run(manager)


@dataclass
class EnvActivate(EnvSubcommand, command_name='activate'):
    """Activate an environment."""


@dataclass
class EnvCreate(EnvSubcommand, command_name='create'):
    """Create a new environment."""
    name: Optional[str] = _get_name_field(required=False)
    packages: list[str] = _get_packages_field()
    force: bool = field(
        default=False,
        metadata={
            'args': ['-f', '--force'],
            'help': 'force overwrite of environment if it exists'
        }
    )

    def _run(self, manager: EnvManager) -> None:
        name = self.name or input('Name of environment: ')
        manager.create(name, packages=self.packages, force=self.force)


@dataclass
class EnvInstall(EnvSubcommand, command_name='install'):
    """Install packages into an environment."""
    packages: list[str] = _get_packages_field()
    # TODO: -d/--distro (base distribution)

    def _run(self, manager: EnvManager) -> None:
        assert self.name is not None
        manager.install(self.name, packages=self.packages)


@dataclass
class EnvRemove(EnvSubcommand, command_name='remove'):
    """Remove an environment."""

    def _run(self, manager: EnvManager) -> None:
        assert self.name is not None
        manager.remove(self.name)


@dataclass
class EnvShow(EnvSubcommand, command_name='show'):
    """Show environments."""
    name: Optional[str] = _get_name_field(required=False)

    def _run(self, manager: EnvManager) -> None:
        manager.show(self.name)


@dataclass
class EnvCmd(CLIDataclass, command_name='env'):
    """Manage environments."""

    subcommand: Union[
        EnvActivate,
        EnvCreate,
        EnvInstall,
        EnvRemove,
        EnvShow
    ] = field(metadata={'subcommand': True})
