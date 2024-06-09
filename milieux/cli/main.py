#!/usr/bin/env python3

from dataclasses import dataclass, field
import sys
import traceback
from typing import Union

from fancy_dataclass import CLIDataclass
from loguru import logger

from milieux import PKG_NAME
from milieux.cli.config import ConfigCmd
from milieux.cli.distro import DistroCmd
from milieux.cli.env import EnvCmd
from milieux.cli.scaffold import ScaffoldCmd
from milieux.config import Config, user_default_config_path
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

    def run(self) -> None:
        """Top-level CLI app for milieux."""
        try:
            config_path = user_default_config_path()
            Config.load_config(config_path)
        except FileNotFoundError:
            if self.subcommand_name != 'config':
                logger.warning(f'Could not find config file {config_path}')
                logger.warning(f"\trun '{PKG_NAME} config new' to create one")
            # use the default config
            Config().update_config()
        try:
            # delegate to subcommand
            super().run()
        except Exception as e:
            if isinstance(e, MilieuxError):  # expected error: just show the message
                msg = str(e)
            else:  # unexpected error: show full traceback
                lines = traceback.format_exception(type(e), e, e.__traceback__)
                msg = ''.join(lines)
            logger.error(msg)
            sys.exit(1)


if __name__ == '__main__':
    MilieuxCLI.main()
