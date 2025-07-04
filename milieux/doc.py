from dataclasses import dataclass
import importlib
from pathlib import Path
from typing import Annotated

from typing_extensions import Doc

from milieux.errors import PackageNotFoundError


DEFAULT_DOC_TEMPLATE = Path(__file__).with_name('doc_template.yml.jinja')


def resolve_package_path(pkg_str: str) -> Path:
    """Resolves a package name to an absolute path."""
    # remove any flags in the package string
    toks = [tok for tok in pkg_str.split() if not tok.startswith('-')]
    if len(toks) != 1:
        raise PackageNotFoundError(pkg_str)
    pkg_str = toks[0]
    if (path := Path(pkg_str)).exists():
        return path
    # TODO: check for the package within an environment?
    try:
        mod = importlib.import_module(pkg_str)
    except ModuleNotFoundError as e:
        raise PackageNotFoundError(pkg_str) from e
    path = Path(mod.__file__)
    if path.name ==  '__init__.py':
        path = path.parent
    return path


@dataclass
class DocSetup:
    """Class for building API reference documentation."""
    site_name: Annotated[str, Doc('Name of top-level documentation page')]
    packages: Annotated[list[str], Doc('List of packages to include in docs')]

    @property
    def package_paths(self) -> list[Path]:
        """Resolves package names to absolute paths."""
        return [resolve_package_path(pkg_str) for pkg_str in self.packages]

    # def render_template(self, template: Path, suffix: Optional[str] = None, extra_vars: Optional[dict[str, Any]] = None) -> None:
    #     """Renders a jinja template, filling in variables from the environment.
    #     If suffix is None, prints the output to stdout.
    #     Otherwise, saves a new file with the original file extension replaced by this suffix.
    #     extra_vars is an optional mapping from extra variables to values."""
    #     # error if unknown variables are present
    #     env = jinja2.Environment(undefined=jinja2.StrictUndefined)
    #     try:
    #         input_template = env.from_string(template.read_text())
    #         kwargs = {**self.template_env_vars, **(extra_vars or {})}
    #         output = input_template.render(**kwargs)
    #     except jinja2.exceptions.TemplateError as e:
    #         msg = f'Error rendering template {template} - {e}'
    #         raise TemplateError(msg) from e
    #     if suffix is None:
    #         print(output)
    #     else:
    #         suffix = suffix if suffix.startswith('.') else ('.' + suffix)
    #         output_path = template.with_suffix(suffix)
    #         output_path.write_text(output)
    #         logger.info(f'Rendered template {template} to {output_path}')
