from dataclasses import dataclass, field
from typing import Any, Optional, Union

from fancy_dataclass.cli import CLIDataclass

from milieux.env import Environment


def _get_name_field(required: bool) -> Any:
    # make 'name' a positional argument
    metadata = {'args': ['name'], 'help': 'name of environment'}
    if not required:
        metadata['nargs'] = '?'
    return field(default=None, metadata=metadata)

_packages_field: Any = field(
    default_factory=list,
    metadata={'nargs': '+', 'args': ['-p', '--packages'], 'help': 'list of packages to install into the environment (can optionally include constraints, e.g. "numpy>=1.25")'}
)

_requirements_field: Any = field(
    default_factory=list,
    metadata={'nargs': '+', 'args': ['-r', '--requirements'], 'help': 'requirements file(s) listing packages'}
)

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
    name: Optional[str] = _get_name_field(required=True)
    packages: list[str] = _packages_field
    requirements: list[str] = _requirements_field
    distros: list[str] = _distros_field
    upgrade: bool = field(default=False, metadata={'help': 'allow package upgrades'})
    editable: Optional[str] = field(
        default=None,
        metadata={'args': ['-e', '--editable'], 'help': 'do an editable install of a single local file'}
    )

    def run(self) -> None:
        assert self.name is not None
        Environment(self.name).install(packages=self.packages, requirements=self.requirements, distros=self.distros, upgrade=self.upgrade, editable=self.editable)


@dataclass
class EnvList(_EnvSubcommand, command_name='list'):
    """List all environments."""

    def run(self) -> None:
        Environment.list()


@dataclass
class EnvNew(EnvSubcommand, command_name='new'):
    """Create a new environment."""
    name: Optional[str] = _get_name_field(required=False)
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
        Environment.new(name, seed=self.seed, python=self.python, force=self.force)


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
class EnvSync(_EnvSubcommand, command_name='sync'):
    """Sync dependencies for an environment.

    NOTE: it is often a good idea to sync from a set of *locked* dependencies (run `milieux distro lock` to create one)."""
    name: Optional[str] = _get_name_field(required=True)
    requirements: list[str] = _requirements_field
    distros: list[str] = _distros_field

    @classmethod
    def parser_description_brief(cls) -> Optional[str]:
        doc = cls.__doc__
        assert isinstance(doc, str)
        return doc.splitlines()[0].lower()[:-1]

    def run(self) -> None:
        assert self.name is not None
        Environment(self.name).sync(requirements=self.requirements, distros=self.distros)


@dataclass
class EnvUninstall(_EnvSubcommand, command_name='uninstall'):
    """Uninstall packages from an environment."""
    name: Optional[str] = _get_name_field(required=True)
    packages: list[str] = _packages_field
    requirements: list[str] = _requirements_field
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
        EnvSync,
        EnvUninstall,
    ] = field(metadata={'subcommand': True})
