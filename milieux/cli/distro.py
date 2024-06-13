from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Optional, Union

from fancy_dataclass.cli import CLIDataclass

from milieux.distro import Distro
from milieux.errors import DistroExistsError
from milieux.utils import NonemptyPrompt, distro_sty


def _get_name_field(required: bool) -> Any:
    # make 'name' a positional argument
    metadata = {'args': ['name'], 'help': 'name of distro'}
    if not required:
        metadata['nargs'] = '?'
    return field(default=None, metadata=metadata)

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
    name: str = _get_name_field(required=True)
    new: Optional[str] = field(default=None, metadata={'nargs': '?', 'const': '', 'help': 'name of new locked distro'})
    force: bool = _force_field
    annotate: bool = field(default=False, metadata={'help': 'include comment annotations indicating the source of each package'})

    def run(self) -> None:
        distro = Distro(self.name)
        if self.new is None:
            new_name = None
        else:
            if self.new == '':
                now = datetime.now()
                new_name = self.name + '.' + now.strftime('%Y%m%d')
            else:
                new_name = self.new
            if (not self.force) and Distro(new_name).exists():
                raise DistroExistsError(f'Distro {distro_sty(new_name)} already exists')
        output = distro.lock(annotate=self.annotate)
        if self.new is None:  # print new file to stdout
            print(output)
        else:
            assert new_name is not None
            Distro.new(new_name, packages=output.splitlines(), force=self.force)


@dataclass
class DistroNew(CLIDataclass, command_name='new'):
    """Create a new distro."""
    name: str = _get_name_field(required=False)
    packages: list[str] = field(
        default_factory=list,
        metadata={'nargs': '+', 'args': ['-p', '--packages'], 'help': 'list of packages to include in the distro'}
    )
    requirements: list[str] = field(
        default_factory=list,
        metadata={'nargs': '+', 'args': ['-r', '--requirements'], 'help': 'requirements file(s) listing packages'}
    )
    distros: list[str] = field(
        default_factory=list,
        metadata={'nargs': '+', 'args': ['-d', '--distros'], 'help': 'existing distro name(s) to include'}
    )
    force: bool = _force_field

    def run(self) -> None:
        name = self.name or NonemptyPrompt.ask('Name of distro')
        if (not self.packages) and (not self.requirements) and (not self.distros):
            packages_str = NonemptyPrompt.ask('Packages to include (comma-separated)')
            packages = [tok.strip() for tok in packages_str.split(',')]
        else:
            packages = self.packages
        Distro.new(name, packages=packages, requirements=self.requirements, distros=self.distros, force=self.force)


@dataclass
class DistroRemove(CLIDataclass, command_name='remove'):
    """Remove a distro."""
    name: str = _get_name_field(required=True)

    def run(self) -> None:
        Distro(self.name).remove()


@dataclass
class DistroShow(CLIDataclass, command_name='show'):
    """Show the contents of a distro."""
    name: str = _get_name_field(required=True)

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
