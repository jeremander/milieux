#!/usr/bin/env python3

from dataclasses import dataclass, field
from pathlib import Path
import sys
import traceback
from typing import Optional, Union

from fancy_dataclass import CLIDataclass
from loguru import logger

from milieux import PKG_NAME
from milieux.cli.config import ConfigCmd
from milieux.cli.distro import DistroCmd
from milieux.cli.env import EnvCmd
from milieux.cli.scaffold import ScaffoldCmd
from milieux.config import Config, set_config_path, user_default_config_path
from milieux.errors import MilieuxError


@dataclass
class MilieuxCLI(CLIDataclass):
    """Tool to assist in developing, building, and installing Python packages."""
    # TODO: use RawDescriptionHelpFormatter, once CLIDataclass supports that
    subcommand: Union[
        ConfigCmd,
        DistroCmd,
        EnvCmd,
        ScaffoldCmd,
     ] = field(metadata={'subcommand': True})
    config: Optional[Path] = field(
        default=None,
        metadata={'args': ['-c', '--config'], 'help': 'path to TOML config file'}
    )

    def _exit_with_error(self, msg: str) -> None:
        if msg:
            logger.error(msg)
        sys.exit(1)

    def _load_config(self) -> None:
        try:
            config_path = self.config or user_default_config_path()
            set_config_path(config_path.absolute())
            Config.load_config(config_path)
        except FileNotFoundError:
            msg = f"Could not find config file {config_path}: run '{PKG_NAME} config new' to create one"
            if config_path != user_default_config_path():
                self._exit_with_error(msg)
            if self.subcommand_name != 'config':
                logger.warning(msg)
            # use the default config
            Config().update_config()
        except ValueError as e:
            self._exit_with_error(f'Invalid config file {config_path}: {e}')

    def _handle_subcommand_error(self, exc: BaseException) -> None:
        if isinstance(exc, MilieuxError):  # expected error: just show the message
            msg = str(exc)
        elif isinstance(exc, (EOFError, KeyboardInterrupt)):  # interrupted user input
            msg = ''
        else:  # unexpected error: show full traceback
            lines = traceback.format_exception(type(exc), exc, exc.__traceback__)
            msg = ''.join(lines)
        self._exit_with_error(msg)

    def run(self) -> None:
        """Top-level CLI app for milieux."""
        self._load_config()
        try:
            super().run()  # delegate to subcommand
        except BaseException as exc:
            self._handle_subcommand_error(exc)


if __name__ == '__main__':
    MilieuxCLI.main()
