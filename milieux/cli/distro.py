from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Optional, Union

from fancy_dataclass.cli import CLIDataclass

from milieux.distro import Distro


_name_field = field(metadata={'help': 'name of distro'})

_force_field = field(
    default=False,
    metadata={
        'args': ['-f', '--force'],
        'help': 'force overwrite of distro if it exists'
    }
)


@dataclass
class DistroList(CLIDataclass, command_name='list'):
    """List all distros."""

    def run(self) -> None:
        Distro.list()


@dataclass
class DistroLock(CLIDataclass, command_name='lock'):
    """Lock dependencies in a distro."""
    name: str = _name_field
    new: Optional[str] = field(default=None, metadata={'nargs': '?', 'const': '', 'help': 'name of new locked distro'})
    force: bool = _force_field
    annotate: bool = field(default=False, metadata={'help': 'include comment annotations indicating the source of each package'})

    def run(self) -> None:
        distro = Distro(self.name)
        output = distro.lock(annotate=self.annotate)
        if self.new is None:  # print new file to stdout
            print(output)
        else:
            if self.new == '':
                now = datetime.now()
                new_name = self.name + '.' + now.strftime('%Y%m%d')
            else:
                new_name = self.new
            Distro.new(new_name, packages=output.splitlines(), force=self.force)


@dataclass
class DistroNew(CLIDataclass, command_name='new'):
    """Create a new distro."""
    name: str = _name_field
    packages: list[str] = field(
        default_factory=list,
        metadata={'nargs': '+', 'help': 'list of packages to include in the distro'}
    )
    requirements: list[str] = field(
        default_factory=list,
        metadata={'nargs': '+', 'args': ['-r', '--requirements'], 'help': 'requirements file(s) listing packages'}
    )
    force: bool = _force_field

    def run(self) -> None:
        reqs = [Path(req) for req in self.requirements]
        Distro.new(self.name, packages=self.packages, requirements=reqs, force=self.force)


@dataclass
class DistroRemove(CLIDataclass, command_name='remove'):
    """Remove a distro."""
    name: str = _name_field

    def run(self) -> None:
        Distro(self.name).remove()


@dataclass
class DistroShow(CLIDataclass, command_name='show'):
    """Show the contents of a distro."""
    name: str = _name_field

    def run(self) -> None:
        Distro(self.name).show()


@dataclass
class DistroCmd(CLIDataclass, command_name='distro'):
    """Manage distros."""
    subcommand: Union[
        DistroList,
        DistroLock,
        DistroNew,
        DistroRemove,
        DistroShow,
    ] = field(metadata={'subcommand': True})
