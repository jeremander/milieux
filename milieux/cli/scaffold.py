from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path
import subprocess
from typing import Literal

from fancy_dataclass.cli import CLIDataclass

from milieux import logger
from milieux.utils import run_command


# utility for scaffolding
ScaffoldUtility = Literal['hatch', 'uv']


class Scaffolder(ABC):
    """Class for setting up a project scaffold."""

    @abstractmethod
    def make_scaffold(self, base_dir: Path, project_name: str) -> None:
        """Creates a scaffold for a new project in the given base directory."""


class HatchScaffolder(Scaffolder):
    """Project scaffolder that uses the 'hatch' command-line tool."""

    def make_scaffold(self, base_dir: Path, project_name: str) -> None:  # noqa: D102
        cmd = ['hatch', 'config', 'find']
        config_path = subprocess.check_output(cmd, text=True).rstrip('\n')
        logger.info(f'Using hatch configurations in {config_path}')
        location = base_dir / project_name
        cmd = ['hatch', 'new', project_name, str(location)]
        run_command(cmd)


class UVScaffolder(Scaffolder):
    """Project scaffolder that uses the 'uv' command-line tool."""

    def make_scaffold(self, base_dir: Path, project_name: str) -> None:  # noqa: D102
        location = base_dir / project_name
        if not location.exists():
            logger.info(f'mkdir {location}')
            location.mkdir()
        cmd = ['uv', 'init', '--directory', str(location), '--verbose']
        run_command(cmd)


SCAFFOLDERS = {
    'hatch': HatchScaffolder,
    'uv': UVScaffolder,
}


@dataclass
class ScaffoldCmd(CLIDataclass, command_name='scaffold'):
    """Set up a project scaffold."""
    project_name: str = field(metadata={'help': 'name of project'})
    utility: ScaffoldUtility = field(default='hatch', metadata={'help': 'utility for creating the scaffold'})

    def run(self) -> None:  # noqa: D102
        cls = SCAFFOLDERS[self.utility]
        scaffolder = cls()
        logger.info(f'Creating new project {self.project_name!r} with {self.utility!r} utility')
        scaffolder.make_scaffold(Path.cwd(), self.project_name)
