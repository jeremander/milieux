from dataclasses import dataclass
from operator import attrgetter
from pathlib import Path
from subprocess import CalledProcessError
import tempfile
from typing import Annotated, Any, Literal

import jinja2
from typing_extensions import Doc

from milieux import logger
from milieux.errors import DocBuildError, NoPackagesError, PackageNotFoundError, TemplateError
from milieux.package import Requirement
from milieux.utils import ensure_dir, run_command


# available themes for mkdocs
MkdocsTheme = Literal['readthedocs', 'material']

DEFAULT_DOC_CONFIG_TEMPLATE = Path(__file__).with_name('doc_template.yml.jinja')
DEFAULT_DOC_HOME_TEMPLATE = Path(__file__).with_name('home_template.md.jinja')
DEFAULT_EXTRA_CSS_TEMPLATE = Path(__file__).with_name('extra.css.jinja')
DEFAULT_SITE_NAME = 'API Docs'
DEFAULT_MKDOCS_THEME: MkdocsTheme = 'readthedocs'


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
    requirements: Annotated[list[Requirement], Doc('List of requirements specifying the packages to include in docs')]
    theme: Annotated[MkdocsTheme, Doc('Name of mkdocs theme to use')] = DEFAULT_MKDOCS_THEME
    config_template: Annotated[Path, Doc('jinja template for mkdocs.yml')] = DEFAULT_DOC_CONFIG_TEMPLATE
    home_template: Annotated[Path, Doc('jinja template for index.md')] = DEFAULT_DOC_HOME_TEMPLATE
    extra_css_template: Annotated[Path, Doc('jinja template for extra.css')] = DEFAULT_EXTRA_CSS_TEMPLATE
    verbose: Annotated[bool, Doc('be verbose')] = False
    allow_missing: Annotated[bool, Doc("warn (don't error) on missing packages")] = False

    def __post_init__(self) -> None:
        # resolve package names to absolute paths
        self._package_paths = []
        for req in self.requirements:
            try:
                self._package_paths.extend(req.get_package_paths())
            except PackageNotFoundError as e:
                if self.allow_missing:
                    logger.warning(str(e))
                else:
                    raise
        if not self._package_paths:
            raise NoPackagesError('No packages found')
        # sort packages by name
        # TODO: should we use naturalsort?
        self._package_paths.sort(key=attrgetter('name'))

    @property
    def template_vars(self) -> dict[str, Any]:
        """Gets a dict from template variables to values."""
        return {
            'SITE_NAME': self.site_name,
            'THEME': self.theme,
            'PKG_PATHS': [str(path) for path in self._package_paths],
            'DEFAULT_SITE_NAME': DEFAULT_SITE_NAME,
        }

    def render_mkdocs_config(self) -> str:
        """Renders the mkdocs.yml config file as a string."""
        return render_template(self.config_template, **self.template_vars)

    def render_mkdocs_index(self) -> str:
        """Renders the index.md homepage Markdown as a string."""
        return render_template(self.home_template, **self.template_vars)

    def render_extra_css(self) -> str:
        """Renders the extra.css file for extra styling, as a string."""
        return render_template(self.extra_css_template, **self.template_vars)

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
        extra_css_path = docs_dir / 'extra.css'
        logger.info(f'Writing {extra_css_path}')
        extra_css_path.write_text(self.render_extra_css())
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
