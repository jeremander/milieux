from dataclasses import dataclass, field
from pathlib import Path
import time
from typing import Literal, Optional, Union

from fancy_dataclass import ArgparseDataclass, CLIDataclass

from milieux import logger
from milieux.distro import get_packages
from milieux.doc import DocSetup


DocFormat = Literal['markdown', 'google', 'numpy', 'restructuredtext']


@dataclass
class PkgArgs(ArgparseDataclass):
    """Specify which packages to build docs for."""
    packages: list[str] = field(
        default_factory=list,
        metadata={'nargs': '+', 'args': ['-p', '--packages'], 'help': 'list of packages'}
    )
    requirements: list[str] = field(
        default_factory=list,
        metadata={'nargs': '+', 'args': ['-r', '--requirements'], 'help': 'requirements file(s) containing packages'}
    )
    distros: list[str] = field(
        default_factory=list,
        metadata={'nargs': '+', 'args': ['-d', '--distros'], 'help': 'existing distro name(s) to include'}
    )

    @property
    def all_packages(self) -> list[str]:
        """Gets a list of all packages."""
        return get_packages(self.packages, self.requirements, self.distros)

    @property
    def default_site_name(self) -> Optional[str]:
        """Gets the default documentation site name if none is provided, based on the packages specified."""
        if (len(self.distros) == 1) and (not self.packages) and (not self.requirements):
            return self.distros[0].title()
        if (len(self.requirements) == 1) and (not self.packages) and (not self.distros):
            return Path(self.requirements[0]).stem.title()
        if (len(self.packages) == 1) and (not self.requirements) and (not self.distros):
            return self.packages[0].title()
        return None


@dataclass
class _DocBuild:
    """Base class for building API documentation using mkdocs."""
    pkg_args: PkgArgs = field(
        default_factory=PkgArgs,
        metadata={'group': 'package arguments'}
    )
    site_name: Optional[str] = field(
        default=None,
        metadata={'help': 'name of top-level site'}
    )
    # TODO: custom mkdocs jinja template

    def __post_init__(self) -> None:
        self._site_name = self.site_name
        if self.site_name is None:  # assign a reasonable default site name
            self._site_name = self.pkg_args.default_site_name

    @property
    def doc_setup(self) -> DocSetup:
        """Gets a DocSetup object for building a mkdocs site."""
        return DocSetup(site_name=self._site_name, packages=self.pkg_args.all_packages)


@dataclass(kw_only=True)
class DocBuild(CLIDataclass, _DocBuild, command_name='build'):
    """Build API documentation."""
    output_dir: Path = field(
        metadata={
            'args': ['-o', '--output-dir'],
            'help': 'save output documentation to this directory'
        }
    )
    # TODO: custom mkdocs config

    def run(self) -> None:
        start = time.perf_counter()
        logger.info(f'Building documentation to {self.output_dir}...')
        setup = self.doc_setup
        print(setup)
        print(setup.package_paths)
        # TODO: build
        elapsed = time.perf_counter() - start
        logger.info(f'Built docs in {elapsed:.3g} sec')


@dataclass
class DocServe(CLIDataclass, _DocBuild, command_name='serve'):
    """Serve API documentation."""
    host: str = field(
        default='localhost',
        metadata={'help': 'host on which to run HTTP server', 'default_help': True}
    )
    port: int = field(
        default=8080,
        metadata={'help': 'port on which to run HTTP serve', 'default_help': True}
    )
    no_browser: bool = field(
        default=False,
        metadata={'help': 'do not open a browser after web server has started'}
    )

    def run(self) -> None:
        logger.info('Serving documentation...')
        # TODO: serve (with or without browser)
        # try:
        #     httpd = pdoc.web.DocServer((self.host, self.port), self.pkg_args.all_packages)
        # except OSError as e:
        #     raise OSError(f'Cannot start web server on {self.host}:{self.port}: {e}') from e
        # with httpd:
        #     url = f'http://{self.host}:{httpd.server_port}'
        #     logger.info(f'Server ready at {url}')
        #     if not self.no_browser:
        #         pdoc.web.open_browser(url)
        #     try:
        #         httpd.serve_forever()
        #     except KeyboardInterrupt:
        #         httpd.server_close()
        #         return


@dataclass
class DocCmd(CLIDataclass, command_name='doc'):
    """Generate API documentation."""
    subcommand: Union[
        DocBuild,
        DocServe,
    ] = field(metadata={'subcommand': True})
