from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Union

from fancy_dataclass import CLIDataclass
from rich.prompt import Confirm, Prompt

from milieux import PROG, logger
from milieux.config import Config, PipConfig, get_config_path, user_default_base_dir
from milieux.errors import ConfigNotFoundError


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
            write = Confirm.ask(prompt)
        if not write:
            return
        default_base_dir = user_default_base_dir()
        base_dir = Prompt.ask('Base directory for workspace', default=str(default_base_dir)).strip()
        if not (p := Path(base_dir)).is_dir():
            prompt = f'Directory {p} does not exist. Create it?'
            create = Confirm.ask(prompt)
            if create:
                p.mkdir(parents=True)
                logger.info(f'Created directory {p}')
            else:
                return
        kwargs: dict[str, Any] = {'base_dir': base_dir}
        default_env_dir = Config.__dataclass_fields__['env_dir'].default
        assert isinstance(default_env_dir, str)
        kwargs['env_dir'] = Prompt.ask('Directory for env_dir', default=default_env_dir).strip()
        # TODO: access ~/.pip/pip.conf to retrieve index_url if it exists
        index_url = Prompt.ask('Default PyPI index URL \\[optional]').strip() or None
        kwargs['pip'] = PipConfig(default_index_url=index_url)
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
