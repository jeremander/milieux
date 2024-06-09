from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Union

from fancy_dataclass import CLIDataclass
from loguru import logger

from milieux import PROG
from milieux.cli import yes_no_prompt
from milieux.config import Config, PipConfig, get_config_path, user_default_base_dir
from milieux.errors import ConfigNotFoundError, UserInputError


@dataclass
class ConfigNew(CLIDataclass, command_name='new'):
    """Create a new config file."""
    stdout: bool = field(
        default=False,
        metadata={'help': 'output config file to stdout'}
    )

    def run(self) -> None:
        """Creates a new config file interactively."""
        path = get_config_path()
        write = True
        if (not self.stdout) and path.exists():
            prompt = f'Config file {path} already exists. Overwrite?'
            write = yes_no_prompt(prompt)
        if not write:
            return
        def prompt_for_dir(descr: str, default_dir: str) -> str:
            return input(f'{descr} [{default_dir}]: ').strip() or default_dir
        default_base_dir = user_default_base_dir()
        base_dir = prompt_for_dir('Base directory for workspace', str(default_base_dir))
        if not Path(base_dir).is_dir():
            # TODO: prompt for creation
            raise UserInputError(f'{base_dir} is not a valid directory')
        kwargs: dict[str, Any] = {'base_dir': base_dir}
        default_env_dir = Config.__dataclass_fields__['env_dir'].default
        assert isinstance(default_env_dir, str)
        kwargs['env_dir'] = prompt_for_dir('Directory for env_dir', default_env_dir)
        # TODO: access ~/.pip/pip.conf to retrieve index_url if it exists
        index_url = input('PyPI index URL (optional): ').strip() or None
        kwargs['pip'] = PipConfig(index_url=index_url)
        cfg = Config(**kwargs)
        if self.stdout:
            print('\n' + cfg.to_toml_string())
        else:
            cfg.save(path)
            logger.info(f'Saved config file to {path}')


@dataclass
class ConfigPath(CLIDataclass, command_name='path'):
    """Print out path to the configurations."""

    def run(self) -> None:
        """Displays the path to the user's config file."""
        print(get_config_path())


@dataclass
class ConfigShow(CLIDataclass, command_name='show'):
    """Show the configurations."""

    def run(self) -> None:
        """Displays the contents of the user's config file."""
        if (path := get_config_path()).exists():
            cfg = Config.load(path)
            print(cfg.to_toml_string())
        else:
            raise ConfigNotFoundError(f"No config file found. Run '{PROG} config new' to create a new one.")


@dataclass
class ConfigCmd(CLIDataclass, command_name='config'):
    """Manage configurations."""

    subcommand: Union[
        ConfigNew,
        ConfigPath,
        ConfigShow,
    ] = field(metadata={'subcommand': True})
