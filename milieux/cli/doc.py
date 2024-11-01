from dataclasses import dataclass, field
from pathlib import Path
from pkgutil import ModuleInfo
import time
from types import ModuleType
from typing import Any, Callable, Literal, Union

from fancy_dataclass import ArgparseDataclass, CLIDataclass
import pdoc.doc
import pdoc.extract
import pdoc.render
import pdoc.web

from milieux import logger
from milieux.distro import get_packages


DocFormat = Literal['markdown', 'google', 'numpy', 'restructuredtext']


def _patch_pdoc() -> None:
    """Override the default `__all__` behavior of pdoc so that it presents all submodules of a package even when it declares an `__all__` member."""
    _iter_modules2: Callable[[ModuleType], dict[str, ModuleInfo]] = pdoc.extract.iter_modules2
    _doc_init = pdoc.doc.Doc.__init__
    def iter_modules2(module: ModuleType) -> dict[str, ModuleInfo]:
        if hasattr(module, '__all__'):
            del module.__all__
        module.__all__ = None  # type: ignore[attr-defined]
        return _iter_modules2(module)
    def doc_init(self: Any, *args: Any, **kwargs: Any) -> None:
        _doc_init(self, *args, **kwargs)
        if hasattr(self.obj, '__all__'):
            del self.obj.__all__
    pdoc.extract.iter_modules2 = iter_modules2
    pdoc.doc.Doc.__init__ = doc_init


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


@dataclass
class RenderArgs(ArgparseDataclass):
    """Customize rendering of docs."""
    # TODO: enable a way to vary the arguments per package
    docformat: DocFormat = field(
        default='markdown',
        metadata={'help': 'docstring format', 'default_help': True}
    )

    def configure(self) -> None:
        """Configures the global pdoc render settings."""
        pdoc.render.configure(docformat=self.docformat)


@dataclass
class DocBuild(CLIDataclass, command_name='build'):
    """Build API documentation."""
    output_dir: Path = field(
        metadata={
            'args': ['-o', '--output-dir'],
            'help': 'save output documentation to this directory'
        }
    )
    pkg_args: PkgArgs = field(
        default_factory=PkgArgs,
        metadata={'group': 'package arguments'}
    )
    render_args: RenderArgs = field(
        default_factory=RenderArgs,
        metadata={'group': 'rendering arguments'}
    )

    def run(self) -> None:
        self.render_args.configure()
        start = time.perf_counter()
        logger.info(f'Building documentation to {self.output_dir}...')
        _patch_pdoc()
        pdoc.pdoc(*self.pkg_args.all_packages, output_directory=self.output_dir)
        elapsed = time.perf_counter() - start
        logger.info(f'Build docs in {elapsed:.3g} sec')


@dataclass
class DocServe(CLIDataclass, command_name='serve'):
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
    pkg_args: PkgArgs = field(
        default_factory=PkgArgs,
        metadata={'group': 'package arguments'}
    )
    render_args: RenderArgs = field(
        default_factory=RenderArgs,
        metadata={'group': 'rendering arguments'}
    )

    def run(self) -> None:
        self.render_args.configure()
        logger.info('Serving documentation...')
        _patch_pdoc()
        try:
            httpd = pdoc.web.DocServer((self.host, self.port), self.pkg_args.all_packages)
        except OSError as e:
            raise OSError(f'Cannot start web server on {self.host}:{self.port}: {e}') from e
        with httpd:
            url = f'http://{self.host}:{httpd.server_port}'
            logger.info(f'Server ready at {url}')
            if not self.no_browser:
                pdoc.web.open_browser(url)
            try:
                httpd.serve_forever()
            except KeyboardInterrupt:
                httpd.server_close()
                return


@dataclass
class DocCmd(CLIDataclass, command_name='doc'):
    """Generate API documentation."""
    subcommand: Union[
        DocBuild,
        DocServe,
    ] = field(metadata={'subcommand': True})
