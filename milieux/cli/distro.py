from dataclasses import dataclass, field
from pathlib import Path
from typing import Union

from fancy_dataclass.cli import CLIDataclass

from milieux.distro import Distro


@dataclass
class DistroList(CLIDataclass, command_name='list'):
    """List all distros."""

    def run(self) -> None:
        Distro.list()


@dataclass
class DistroNew(CLIDataclass, command_name='new'):
    """Create a new distro."""
    name: str = field(metadata={'help': 'name of distro'})
    packages: list[str] = field(
        default_factory=list,
        metadata={'nargs': '+', 'help': 'list of packages to include in the distro'}
    )
    requirements: list[str] = field(
        default_factory=list,
        metadata={'nargs': '+', 'args': ['-r', '--requirements'], 'help': 'requirements file(s) listing packages'}
    )
    force: bool = field(
        default=False,
        metadata={
            'args': ['-f', '--force'],
            'help': 'force overwrite of distro if it exists'
        }
    )

    def run(self) -> None:
        reqs = [Path(req) for req in self.requirements]
        Distro.new(self.name, packages=self.packages, requirements=reqs, force=self.force)


@dataclass
class DistroShow(CLIDataclass, command_name='show'):
    """Show the contents of a distro."""
    name: str = field(metadata={'help': 'name of distro'})

    def run(self) -> None:
        Distro(self.name).show()


@dataclass
class DistroCmd(CLIDataclass, command_name='distro'):
    """Manage distros."""
    subcommand: Union[
        DistroList,
        DistroNew,
        DistroShow,
    ] = field(metadata={'subcommand': True})
