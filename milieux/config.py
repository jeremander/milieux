from dataclasses import dataclass, field
from pathlib import Path
from typing import Annotated, Optional

from fancy_dataclass import ConfigDataclass, TOMLDataclass
from typing_extensions import Doc  # type: ignore[attr-defined]

from milieux import PKG_NAME
from milieux.utils import resolve_path


#################
# DEFAULT PATHS #
#################

def user_dir() -> Path:
    """Gets the path to the user's directory where configs, etc. will be stored."""
    return Path.home() / f'.{PKG_NAME}'

def user_default_config_path() -> Path:
    """Gets the default path to the user's config file."""
    return user_dir() / 'config.toml'

def user_default_base_dir() -> Path:
    """Gets the default path to the user's base workspace directory."""
    return user_dir() / 'workspace'


##########
# CONFIG #
##########

@dataclass
class PipConfig(TOMLDataclass):
    """Configurations for pip."""
    index_url: Annotated[
        Optional[str],
        Doc('URL for PyPI index')
    ] = None


@dataclass
class Config(ConfigDataclass, TOMLDataclass):  # type: ignore[misc]
    """Configurations for milieux."""
    base_dir: Annotated[
        str,
        Doc('base directory (by default, everything will be installed here)')
    ] = field(default_factory=lambda: str(user_default_base_dir()))
    env_dir: Annotated[
        str,
        Doc('directory for virtual environments')
    ] = 'envs'
    module_dir: Annotated[
        str,
        Doc('directory for module files')
    ] = 'modules'
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
    def module_dir_path(self) -> Path:
        """Gets the path to the TCL module directory."""
        return resolve_path(self.module_dir, Path(self.base_dir))