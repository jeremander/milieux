from argparse import RawDescriptionHelpFormatter
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional, Union

from fancy_dataclass.cli import CLIDataclass

from milieux.env import TEMPLATE_ENV_VARS, Environment
from milieux.errors import NoSuchTemplateError, UserInputError


def _get_name_field(required: bool) -> Any:
    # make 'name' a positional argument
    metadata = {'args': ['name'], 'help': 'name of environment'}
    if not required:
        metadata['nargs'] = '?'
    return field(default=None, metadata=metadata)

_packages_field: Any = field(
    default_factory=list,
    metadata={'nargs': '+', 'args': ['-p', '--packages'], 'help': 'list of packages to install into the environment (can optionally include constraints, e.g. "numpy>=1.25")'}
)

_requirements_field: Any = field(
    default_factory=list,
    metadata={'nargs': '+', 'args': ['-r', '--requirements'], 'help': 'requirements file(s) listing packages'}
)

_distros_field: Any = field(
    default_factory=list,
    metadata={'nargs': '+', 'args': ['-d', '--distros'], 'help': 'distro name(s) providing packages'}
)


@dataclass
class _EnvSubcommand(CLIDataclass):

    def run(self) -> None:
        raise NotImplementedError


@dataclass
class EnvSubcommand(_EnvSubcommand):
    """Base class for environment subcommands."""
    name: Optional[str] = _get_name_field(required=True)


@dataclass
class EnvActivate(EnvSubcommand, command_name='activate'):
    """Activate an environment."""
    name: Optional[str] = _get_name_field(required=True)

    def run(self) -> None:
        name = self.name or input('Name of environment: ')
        Environment(name).activate()


@dataclass
class EnvFreeze(EnvSubcommand, command_name='freeze'):
    """List installed packages in an environment."""
    name: str = _get_name_field(required=True)

    def run(self) -> None:
        Environment(self.name).freeze()


@dataclass
class EnvInstall(_EnvSubcommand, command_name='install'):
    """Install packages into an environment."""
    name: Optional[str] = _get_name_field(required=True)
    packages: list[str] = _packages_field
    requirements: list[str] = _requirements_field
    distros: list[str] = _distros_field
    upgrade: bool = field(default=False, metadata={'help': 'allow package upgrades'})
    editable: Optional[str] = field(
        default=None,
        metadata={'args': ['-e', '--editable'], 'help': 'do an editable install of a single local file'}
    )

    def run(self) -> None:
        assert self.name is not None
        Environment(self.name).install(packages=self.packages, requirements=self.requirements, distros=self.distros, upgrade=self.upgrade, editable=self.editable)


@dataclass
class EnvList(_EnvSubcommand, command_name='list'):
    """List all environments."""

    def run(self) -> None:
        Environment.list()


@dataclass
class EnvNew(EnvSubcommand, command_name='new'):
    """Create a new environment."""
    name: Optional[str] = _get_name_field(required=False)
    seed: bool = field(
        default=False,
        metadata={'help': 'install "seed" packages (e.g. `pip`) into environment'}
    )
    python: Optional[str] = field(
        default=None,
        metadata={'args': ['-p', '--python'], 'help': 'Python interpreter for the environment'}
    )
    force: bool = field(
        default=False,
        metadata={
            'args': ['-f', '--force'],
            'help': 'force overwrite of environment if it exists'
        }
    )

    def run(self) -> None:
        name = self.name or input('Name of environment: ')
        Environment.new(name, seed=self.seed, python=self.python, force=self.force)


@dataclass
class EnvRemove(EnvSubcommand, command_name='remove'):
    """Remove an environment."""

    def run(self) -> None:
        assert self.name is not None
        Environment(self.name).remove()


@dataclass
class EnvShow(EnvSubcommand, command_name='show'):
    """Show info about an environment."""
    name: str = _get_name_field(required=True)
    list_packages: bool = field(default=False, metadata={'help': 'include list of installed packages'})

    def run(self) -> None:
        Environment(self.name).show(list_packages=self.list_packages)


@dataclass
class EnvSync(_EnvSubcommand,
    command_name='sync',
    formatter_class=RawDescriptionHelpFormatter,
    help_descr_brief='sync dependencies for an environment'
):
    """Sync dependencies for an environment.

NOTE: it is often a good idea to sync from a set of *locked* dependencies.
Run `milieux distro lock` to create one."""
    name: Optional[str] = _get_name_field(required=True)
    requirements: list[str] = _requirements_field
    distros: list[str] = _distros_field

    def run(self) -> None:
        assert self.name is not None
        Environment(self.name).sync(requirements=self.requirements, distros=self.distros)


_env_template_descr = 'Render one or more jinja templates, filling in variables from an environment.\n\nThe following variables from the environment may be used in {{ENV_VARIABLE}}\nexpressions within your template:\n'
_env_template_descr += '\n'.join(f'\t{key}: {val}' for (key, val) in TEMPLATE_ENV_VARS.items())
_env_template_descr += '\n\nExtra variables may be provided via the --extra-vars argument.'

@dataclass
class EnvTemplate(EnvSubcommand,
    command_name='template',
    formatter_class=RawDescriptionHelpFormatter,
    help_descr=_env_template_descr,
):
    """Render a template, filling in variables from an environment."""
    # TODO: list variables in docstring
    templates: list[Path] = field(
        default_factory=list,
        metadata={'args': ['-t', '--templates'], 'required': True, 'nargs': '+', 'help': 'jinja template(s) to render'}
    )
    suffix: Optional[str] = field(
        default=None,
        metadata={'help': 'suffix to replace template file extensions for output'}
    )
    extra_vars: list[str] = field(
        default_factory=list,
        metadata={'nargs': '+', 'help': 'extra variables to pass to template, format is: "VAR1=VALUE1 VAR2=VALUE2 ..."'}
    )

    def __post_init__(self) -> None:
        # parse extra_vars
        extra_vars = {}
        for tok in self.extra_vars:
            if '=' in tok:
                [key, val] = tok.split('=', maxsplit=1)
                if key in extra_vars:
                    raise UserInputError(f'Duplicate variable {key!r} in --extra-vars')
                extra_vars[key] = val
            else:
                raise UserInputError(f'Invalid VARIABLE=VALUE string: {tok}')
        self._extra_vars = extra_vars

    def run(self) -> None:
        assert self.name is not None
        if (not self.suffix) and (len(self.templates) > 1):
            raise UserInputError('When rendering multiple templates, you must set a --suffix for output files')
        for template in self.templates:
            if not template.is_file():
                raise NoSuchTemplateError(template)
        env = Environment(self.name)
        for template in self.templates:
            env.render_template(template=template, suffix=self.suffix, extra_vars=self._extra_vars)


@dataclass
class EnvUninstall(_EnvSubcommand, command_name='uninstall'):
    """Uninstall packages from an environment."""
    name: Optional[str] = _get_name_field(required=True)
    packages: list[str] = _packages_field
    requirements: list[str] = _requirements_field
    distros: list[str] = _distros_field

    def run(self) -> None:
        assert self.name is not None
        Environment(self.name).uninstall(packages=self.packages, requirements=self.requirements, distros=self.distros)


@dataclass
class EnvCmd(CLIDataclass, command_name='env'):
    """Manage environments."""

    subcommand: Union[
        EnvActivate,
        EnvFreeze,
        EnvInstall,
        EnvList,
        EnvNew,
        EnvRemove,
        EnvShow,
        EnvSync,
        EnvTemplate,
        EnvUninstall,
    ] = field(metadata={'subcommand': True})
