from dataclasses import dataclass

from fancy_dataclass import CLIDataclass


@dataclass
class BuildDocsCmd(CLIDataclass, command_name='build-docs'):
    """Build API documentation."""

    def run(self) -> None:
        print('Building docs...')
