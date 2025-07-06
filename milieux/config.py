from dataclasses import dataclass, field
from pathlib import Path
from typing import Annotated, Optional

from fancy_dataclass import ConfigDataclass, TOMLDataclass
from typing_extensions import Doc

from milieux import PKG_NAME
from milieux.errors import ConfigNotFoundError
from milieux.utils import resolve_path


#################
# DEFAULT PATHS #
#################

def user_dir() -> Path:
    """Gets the path to the user's directory where configs, etc. will be stored."""
    return Path.home() / '.config' / PKG_NAME

def user_default_config_path() -> Path:
    """Gets the default path to the user's config file."""
    return user_dir() / 'config.toml'

def user_default_base_dir() -> Path:
    """Gets the default path to the user's base workspace directory."""
    return user_dir() / 'workspace'

# global variable storing the config path
_CONFIG_PATH: Optional[Path] = None

def get_config_path() -> Path:
    """Gets the global configuration path."""
    return _CONFIG_PATH or user_default_config_path()

def set_config_path(cfg_path: Path) -> None:
    """Sets the global configuration path."""
    global _CONFIG_PATH
    _CONFIG_PATH = cfg_path


##########
# CONFIG #
##########

@dataclass
class PipConfig(TOMLDataclass):
    """Configurations for pip."""
    default_index_url: Annotated[
        Optional[str],
        Doc('URL for default PyPI index')
    ] = None
    index_urls: Annotated[
        Optional[list[str]],
        Doc('additional package index URLs (will be checked in order, with priority over the default index)'),
    ] = None

    @property
    def uv_args(self) -> list[str]:
        """Gets additional arguments for a `uv` command to set the index URLs appropriately."""
        args = []
        if self.default_index_url:
            args.extend(['--default-index', self.default_index_url])
        for url in (self.index_urls or []):
            args.extend(['--index', url])
        return args


@dataclass
class Config(ConfigDataclass, TOMLDataclass):
    """Configurations for milieux."""
    base_dir: Annotated[
        str,
        Doc('base directory (by default, everything will be installed here)')
    ] = field(default_factory=lambda: str(user_default_base_dir()))
    env_dir: Annotated[
        str,
        Doc('directory for virtual environments')
    ] = 'envs'
    distro_dir: Annotated[
        str,
        Doc('directory for distros (Python requirements files)')
    ] = 'distros'
    pip: PipConfig = field(default_factory=PipConfig)

    @property
    def base_dir_path(self) -> Path:
        """Gets the path to the base workspace directory."""
        return Path(self.base_dir)

    @property
    def env_dir_path(self) -> Path:
        """Gets the path to the environment directory."""
        return resolve_path(self.env_dir, Path(self.base_dir))

    @property
    def distro_dir_path(self) -> Path:
        """Gets the path to the distro directory."""
        return resolve_path(self.distro_dir, Path(self.base_dir))


def get_config() -> Config:
    """Gets the current configurations.
    If none are set, loads them from the user's default config path."""
    cfg = Config.get_config()
    if cfg is None:
        config_path = user_default_config_path()
        try:
            cfg = Config.load_config(config_path)
        except FileNotFoundError as e:
            raise ConfigNotFoundError(f'Could not load configs from {config_path}') from e
        set_config_path(config_path)
        cfg.update_config()
    return cfg
