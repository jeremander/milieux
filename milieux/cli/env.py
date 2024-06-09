from dataclasses import dataclass, field
from typing import Any, Optional, Union

from fancy_dataclass.cli import CLIDataclass

from milieux.env import Environment


def _get_name_field(required: bool) -> Any:
    metadata = {'args': ['-n', '--name'], 'required': required, 'help': 'name of environment'}
    return field(default=None, metadata=metadata)

_packages_field_help = 'list of packages to install into the environment (can optionally include constraints, e.g. "numpy>=1.25")'

_distros_field: Any = field(
    default_factory=list,
    metadata={'nargs': '+', 'args': ['-d', '--distros'], 'help': 'distro name(s) providing packages'}
)


@dataclass
class _EnvSubcommand(CLIDataclass):

    def run(self) -> None:
        raise NotImplementedError


@dataclass
class EnvSubcommand(_EnvSubcommand):
    """Base class for environment subcommands."""
    name: Optional[str] = _get_name_field(required=True)


@dataclass
class EnvActivate(EnvSubcommand, command_name='activate'):
    """Activate an environment."""
    name: Optional[str] = _get_name_field(required=True)

    def run(self) -> None:
        name = self.name or input('Name of environment: ')
        Environment(name).activate()


@dataclass
class EnvFreeze(EnvSubcommand, command_name='freeze'):
    """List installed packages in an environment."""
    name: str = _get_name_field(required=True)

    def run(self) -> None:
        Environment(self.name).freeze()


@dataclass
class EnvInstall(_EnvSubcommand, command_name='install'):
    """Install packages into an environment."""
    packages: list[str] = field(metadata={'help': _packages_field_help})
    name: Optional[str] = _get_name_field(required=True)
    requirements: list[str] = field(
        default_factory=list,
        metadata={'nargs': '+', 'args': ['-r', '--requirements'], 'help': 'requirements file(s) listing packages'}
    )
    distros: list[str] = _distros_field

    def run(self) -> None:
        assert self.name is not None
        Environment(self.name).install(packages=self.packages, requirements=self.requirements, distros=self.distros)


@dataclass
class EnvList(_EnvSubcommand, command_name='list'):
    """List all environments."""

    def run(self) -> None:
        Environment.list()


@dataclass
class EnvNew(EnvSubcommand, command_name='new'):
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

    def run(self) -> None:
        name = self.name or input('Name of environment: ')
        Environment.new(name, packages=self.packages, seed=self.seed, python=self.python, force=self.force)


@dataclass
class EnvRemove(EnvSubcommand, command_name='remove'):
    """Remove an environment."""

    def run(self) -> None:
        assert self.name is not None
        Environment(self.name).remove()


@dataclass
class EnvShow(EnvSubcommand, command_name='show'):
    """Show info about an environment."""
    name: str = _get_name_field(required=True)
    list_packages: bool = field(default=False, metadata={'help': 'include list of installed packages'})

    def run(self) -> None:
        Environment(self.name).show(list_packages=self.list_packages)


@dataclass
class EnvUninstall(_EnvSubcommand, command_name='uninstall'):
    """Uninstall packages from an environment."""
    packages: list[str] = field(metadata={'help': _packages_field_help})
    name: Optional[str] = _get_name_field(required=True)
    requirements: list[str] = field(
        default_factory=list,
        metadata={'nargs': '+', 'args': ['-r', '--requirements'], 'help': 'requirements file(s) listing packages'}
    )
    distros: list[str] = _distros_field

    def run(self) -> None:
        assert self.name is not None
        Environment(self.name).uninstall(packages=self.packages, requirements=self.requirements, distros=self.distros)


@dataclass
class EnvCmd(CLIDataclass, command_name='env'):
    """Manage environments."""

    subcommand: Union[
        EnvActivate,
        EnvFreeze,
        EnvInstall,
        EnvList,
        EnvNew,
        EnvRemove,
        EnvShow,
        EnvUninstall,
    ] = field(metadata={'subcommand': True})
