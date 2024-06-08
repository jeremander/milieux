from dataclasses import dataclass, field
from pathlib import Path
from typing import Union

from fancy_dataclass.cli import CLIDataclass

from milieux.distro import Distro


# @dataclass
# class DisSubcommand(_EnvSubcommand):
#     """Base class for environment subcommands."""
#     name: Optional[str] = _get_name_field(required=True)

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
class DistroCmd(CLIDataclass, command_name='distro'):
    """Manage distros."""

    subcommand: Union[
        DistroNew,
        # DistroList,
    ] = field(metadata={'subcommand': True})
