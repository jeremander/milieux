#!/usr/bin/env python3

from dataclasses import dataclass, field
from pathlib import Path
import sys
import traceback
from typing import Optional, Union

from fancy_dataclass import CLIDataclass

from milieux import PROG, __version__, logger
from milieux.cli.config import ConfigCmd
from milieux.cli.distro import DistroCmd
from milieux.cli.doc import DocCmd
from milieux.cli.env import EnvCmd
from milieux.cli.scaffold import ScaffoldCmd
from milieux.config import Config, set_config_path, user_default_config_path
from milieux.errors import MilieuxError


def _exit_with_error(msg: str) -> None:
    if msg:
        logger.error(f'[bold red]ERROR[/] - [red]{msg}[/]')
    sys.exit(1)

def _handle_error(exc: BaseException) -> None:
    if isinstance(exc, MilieuxError):  # expected error: just show the message
        msg = str(exc)
    elif isinstance(exc, (EOFError, KeyboardInterrupt)):  # interrupted user input
        msg = ''
    elif isinstance(exc, SystemExit):
        raise
    else:  # no cov
        # unexpected error: show full traceback
        lines = traceback.format_exception(type(exc), exc, exc.__traceback__)
        msg = ''.join(lines)
    _exit_with_error(msg)


@dataclass
class MilieuxCLI(CLIDataclass, version=f'%(prog)s {__version__}'):
    """Tool to assist in developing, building, and installing Python packages."""
    subcommand: Union[
        ConfigCmd,
        DistroCmd,
        DocCmd,
        EnvCmd,
        ScaffoldCmd,
     ] = field(metadata={'subcommand': True})
    config: Optional[Path] = field(
        default=None,
        metadata={'args': ['-c', '--config'], 'help': 'path to TOML config file'}
    )

    def _load_config(self) -> None:
        try:
            config_path = self.config or user_default_config_path()
            set_config_path(config_path.absolute())
            Config.load_config(config_path)
        except FileNotFoundError:
            msg = f"Could not find config file {config_path}: run '{PROG} config new' to create one"
            if config_path != user_default_config_path():
                _exit_with_error(msg)
            if self.subcommand_name != 'config':
                logger.warning(msg)
            # use the default config
            Config().update_config()
        except ValueError as e:
            _exit_with_error(f'Invalid config file {config_path}: {e}')

    def run(self) -> None:
        """Top-level CLI app for milieux."""
        self._load_config()
        super().run()

    @classmethod
    def main(cls, arg_list: Optional[list[str]] = None) -> None:
        """Add custom error handling to main function to exit gracefully when possible."""
        try:
            super().main(arg_list=arg_list)  # delegate to subcommand
        except BaseException as exc:
            _handle_error(exc)


if __name__ == '__main__':
    MilieuxCLI.main()
