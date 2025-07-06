from dataclasses import dataclass
import importlib
from pathlib import Path
from subprocess import CalledProcessError
import tempfile
from typing import Annotated, Any

import jinja2
import tomli  # TODO: use tomllib once minimum Python 3.11 is supported
from typing_extensions import Doc

from milieux import logger
from milieux.errors import DocBuildError, PackageNotFoundError, TemplateError
from milieux.utils import ensure_dir, run_command


DEFAULT_DOC_CONFIG_TEMPLATE = Path(__file__).with_name('doc_template.yml.jinja')
DEFAULT_DOC_HOME_TEMPLATE = Path(__file__).with_name('home_template.md.jinja')
DEFAULT_SITE_NAME = 'API Docs'


def resolve_local_package_path(path: Path) -> Path:
    """Given a path to a local Python project, resolves the top-level package path."""
    root = Path(path).resolve()
    pyproject_path = root / 'pyproject.toml'
    if pyproject_path.exists():
        with pyproject_path.open('rb') as f:
            data = tomli.load(f)
        # try PEP 621 first
        if (name := data.get('project', {}).get('name')):
            name = name.replace('-', '_')
            # infer package dir from name
            p: Path = root / name
            if p.is_dir():
                return p
            # next, try src subdirectory
            src_dir = root / 'src'
            if src_dir.is_dir():
                p = src_dir / name
                if p.is_dir():
                    return p
    # fallback: look for any subdir with __init__.py
    for child in root.iterdir():
        if child.name.startswith('test'):
            continue
        if (child / '__init__.py').exists():
            return child
    raise FileNotFoundError(f'No package dir found in {path}')

def resolve_package_path(pkg_str: str) -> Path:
    """Resolves a package name to an absolute path."""
    # remove any flags in the package string
    toks = [tok for tok in pkg_str.split() if not tok.startswith('-')]
    if len(toks) != 1:
        raise PackageNotFoundError(pkg_str)
    pkg_str = toks[0]
    if '/' in pkg_str:  # pkg_str is a path
        if (path := Path(pkg_str)).exists():
            # resolve local package directory
            try:
                return resolve_local_package_path(path)
            except FileNotFoundError as e:
                raise PackageNotFoundError(pkg_str) from e
        raise PackageNotFoundError(pkg_str)
    # TODO: check for the package within an environment?
    try:
        mod = importlib.import_module(pkg_str)
    except ModuleNotFoundError as e:
        raise PackageNotFoundError(pkg_str) from e
    if mod.__file__ is None:
        raise PackageNotFoundError(pkg_str)
    path = Path(mod.__file__)
    if path.name ==  '__init__.py':
        path = path.parent
    return path

def render_template(template: Path, **template_vars: Any) -> str:
    """Renders a jinja template with the given template variables as a string."""
    env = jinja2.Environment(undefined=jinja2.StrictUndefined)
    try:
        input_template = env.from_string(template.read_text())
        return input_template.render(**template_vars)
    except jinja2.exceptions.TemplateError as e:
        msg = f'Error rendering template {template} - {e}'
        raise TemplateError(msg) from e


@dataclass
class DocSetup:
    """Class for building API reference documentation."""
    site_name: Annotated[str, Doc('Name of top-level documentation page')]
    packages: Annotated[list[str], Doc('List of packages to include in docs')]
    config_template: Annotated[Path, Doc('jinja template for mkdocs.yml')] = DEFAULT_DOC_CONFIG_TEMPLATE
    home_template: Annotated[Path, Doc('jinja template for index.md')] = DEFAULT_DOC_HOME_TEMPLATE
    verbose: Annotated[bool, Doc('be verbose')] = False

    @property
    def package_paths(self) -> list[Path]:
        """Resolves package names to absolute paths."""
        return [resolve_package_path(pkg_str) for pkg_str in self.packages]

    @property
    def template_vars(self) -> dict[str, Any]:
        """Gets a dict from template variables to values."""
        return {
            'SITE_NAME': self.site_name,
            'PKG_PATHS': [str(path) for path in self.package_paths],
            'DEFAULT_SITE_NAME': DEFAULT_SITE_NAME,
        }

    def render_mkdocs_config(self) -> str:
        """Renders the mkdocs.yml config file as a string."""
        return render_template(self.config_template, **self.template_vars)

    def render_mkdocs_index(self) -> str:
        """Renders the index.md homepage Markdown as a string."""
        return render_template(self.home_template, **self.template_vars)

    def setup_mkdocs(self, output_dir: Path) -> Path:
        """Sets up the directory in which to run mkdocs, writing mkdocs.yml (config file) and index.md (homepage).
        Returns the path to the config file."""
        _ = ensure_dir(output_dir)
        docs_dir = ensure_dir(output_dir / 'docs')
        config_path = output_dir / 'mkdocs.yml'
        logger.info(f'Writing {config_path}')
        config_path.write_text(self.render_mkdocs_config())
        index_path = docs_dir / 'index.md'
        logger.info(f'Writing {index_path}')
        index_path.write_text(self.render_mkdocs_index())
        return config_path

    def _run_command(self, cmd: list[str]) -> None:
        try:
            _ = run_command(cmd, check=True, capture_output=(not self.verbose))
        except CalledProcessError as e:
            msg = '' if (e.stderr is None) else e.stderr.rstrip()
            raise DocBuildError(msg) from e

    def build_docs(self, output_dir: Path) -> None:
        """Builds the API documentation in the given output directory."""
        config_path = self.setup_mkdocs(output_dir)
        cmd = ['mkdocs', 'build', '-f', str(config_path)]
        self._run_command(cmd)

    def serve_docs(self, host: str = 'localhost', port: int = 800, no_browser: bool = False) -> None:
        """Serves the API documentation on a live server."""
        with tempfile.TemporaryDirectory(dir='.') as td:
            output_dir = Path(td)
            config_path = self.setup_mkdocs(output_dir)
            addr = f'{host}:{port}'
            cmd = ['mkdocs', 'serve', '-f', str(config_path), '--dev-addr', addr]
            if not no_browser:
                cmd.append('--open')
            self._run_command(cmd)
