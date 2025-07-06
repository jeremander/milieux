# Milieux

[![PyPI - Version](https://img.shields.io/pypi/v/milieux)](https://pypi.org/project/milieux)
![GitHub Actions Workflow Status](https://img.shields.io/github/actions/workflow/status/jeremander/milieux/workflow.yml)
![Coverage Status](https://github.com/jeremander/milieux/raw/coverage-badge/coverage-badge.svg)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://raw.githubusercontent.com/jeremander/milieux/main/LICENSE)
[![pre-commit](https://img.shields.io/badge/pre--commit-enabled-brightgreen?logo=pre-commit)](https://github.com/pre-commit/pre-commit)

A general-purpose tool to assist in developing, building, and installing Python packages.

⚠️ `milieux` is currently in its very early stages and should *not* be considered stable.

## Introduction

`milieux` is a tool used for managing multiple [virtual environments](https://realpython.com/python-virtual-environments-a-primer/#why-do-you-need-virtual-environments) and *distributions*.

We define a *distribution* (or "distro") to be a collection of Python packages you often want bundled together. For example, you might want to bundle `numpy`, `scipy`, and `pandas` together into a distribution named `scientific`, which you can then install into one more more virtual environments. To do this, you can run:

```shell
milieux distro new scientific -p numpy scipy pandas
```

Then to create a new environment `my_env` and install all dependencies from this distribution:

```shell
milieux env new my_env

milieux env install -d scientific
```

## Installation

```shell
pip install milieux
```

### Dependencies

- 🦀 [uv](https://github.com/astral-sh/uv), an ultra-fast package resolver and installer written in Rust.

- 🐍 [hatch](https://github.com/pypa/hatch), for building/publishing packages.

- 🤵🏻‍♂️ [fancy_dataclass](https://fancy-dataclass.readthedocs.io/en/latest/), for configurations and argument parsing.

- 📄 [mkdocs](https://www.mkdocs.org), for documentation generation.

- 💰 [rich](https://rich.readthedocs.io/en/stable/index.html), for text and table styling.

## Usage

View help menu:

```shell
milieux -h
```

View subcommand help menu:

```text
milieux <SUBCOMMAND> -h
```

For brevity, you may want to alias the command as follows:

```shell
alias mlx="milieux"
```

Then you can type `mlx` in place of the full (tricky-to-spell) name.

## Commands

Here is a quick tour of the commands available in `milieux`.

### `distro`: Manage distributions

`milieux distro` has a collection of subcommands for creating, viewing, and modifying distributions (distros), which are collections of Python packages.

A distro is nothing more than a *requirements file*, a plaintext file containing a list of Python packages. See the [specification](https://pip.pypa.io/en/stable/reference/requirements-file-format/) for more details about how to specify package URLs, versions, etc.

| Subcommand  | Description |
| ----------- | ----------- |
| `list`      | List all distros |
| `lock`      | Lock dependencies |
| `new`       | Create new distro |
| `remove`    | Remove a distro |
| `show`      | Show contents of a distro |

#### Locking dependencies

`milieux distro lock` can be used to "lock" or "pin" the packages listed in a distro (requirements) file. This calls the dependency resolver to figure out the latest versions of all the packages that are mutually compatible. It then saves them out to a new requirements file.

Locking dependencies can ensure reproducibility of environments (someone else can set up the exact same environment, regardless of what the latest package versions happen to be). The downside is that the locked dependencies may become out of date.

**Example**: from the earlier `scientific` distro example, lock dependencies to the current versions, and save them to a new distro marked with the current date.

```text
$ milieux distro lock scientific --new scientific.20240609

Locking dependencies for 'scientific' distro
...
Creating distro 'scientific.20240609'

$ milieux distro show scientific.20240609

...
numpy==1.26.4
pandas==2.2.2
python-dateutil==2.9.0.post0
pytz==2024.1
scipy==1.13.1
six==1.16.0
tzdata==2024.1
```

### `env`: Manage environments

`milieux env` has a collection of subcommands for creating, viewing, and modifying virtual environments.

| Subcommand  | Description |
| ----------- | ----------- |
| `activate`  | Activate an environment |
| `freeze`    | List installed packages |
| `install`   | Install packages |
| `list`      | List all environments |
| `new`       | Create new environment |
| `remove`    | Remove an environment |
| `show`      | Show environment info |
| `sync`      | Sync dependencies |
| `template`  | Render a [jinja](https://jinja.palletsprojects.com/) template, filling in variables from an environment |
| `uninstall` | Uninstall packages |

#### Activate an environment

`milieux env activate` provides an easy way to activate a virtual environment. Unfortunately it is awkward to source an activation script directly from Python, so this command actually just prints out instructions for how to activate the environment.

However, you can also activate the environment directly by calling the command within backticks (which executes its output). For example:

```shell
`milieux env activate my_env`
```

This will source the activation script associated with the `my_env` virtual environment. To deactivate the environment, run `deactivate`.

#### Install packages

`milieux env install` lets you install packages into an environment. You can list specific packages with `-p`, requirements files with `-r`, or distro names with `-d`.

**Example**: install packages from the `scientific` distro, plus `scikit-learn` and PyTorch.

```shell
milieux env install my_env -d scientific -p scikit-learn torch
```

If you are already in an activated environment, you may omit the name of the environment, and it will assume the active one:

```shell
milieux env install -p pandas
```

#### Sync packages

`milieux env sync` is similar to `install`, but instead of installing new packages, it will *sync* them to the environment, making sure these are the *only* packages in the environment. This is ideal for controlling exactly what version of each specific package you want (see: [locking dependencies](#locking-dependencies)).

<!--
#### Render template file for an environment

TODO: include a description of `milieux env template` (this may be TMI).
-->

### `scaffold`: Create project scaffold

`milieux scaffold` creates a new Python project from a default or custom scaffold.

```shell
milieux scaffold my_project
```

The command above will create a new project in a `my_project` subdirectory.

The `--utility` argument lets you specify the utility for creating the project scaffold.

🚧 At present, the only supported scaffold utility is [hatch](https://hatch.pypa.io/latest). In the future we plan to support arbitrary project templates via [jinja](https://jinja.palletsprojects.com/) and/or [cookiecutter](https://cookiecutter.readthedocs.io/en/stable/).

### `doc`: Create API reference documentation

`milieux doc` builds API reference documentation for one or more packages.

**Example**: build docs for all packages in a distro, saving them to a `docs/` directory:

```shell
milieux doc build -d my_distro -o docs
```

**Example**: serve documentation on `localhost` for a single package:

```shell
milieux doc serve -p my_package
```

This uses [mkdocs](https://www.mkdocs.org), [mkdocs-material](https://squidfunk.github.io/mkdocs-material/), and [mkdocs-api-autonav](https://github.com/tlambert03/mkdocs-api-autonav/) to produce the documentation.

#### Customization

`milieux` does not (yet) expose much in the way of customization, but some things may be controlled using [jinja](https://jinja.palletsprojects.com/) templates.

To customize the `mkdocs` settings, you can provide a jinja YAML template file to `--config-template`. The default is [doc_template.yml.jinja](milieux/doc/doc_template.yml.jinja).

To customize the home page (`index.html`), you can provide a jinja Markdown template file to `--home-template`. The default is [home_template.md.jinja](milieux/doc/home_template.md.jinja).

Two template variables may be used within the templates. Their values will be passed in based on other command-line arguments:

- `SITE_NAME`: based on `--site-name` (if provided), or the distro/package name (if there is only one), or the default name "API Docs" otherwise.
- `PKG_PATHS`: list of paths to each of the packages to be included in the reference docs. This is derived from the list of distros, requirements, and packages provided by the user.

### `config`: Manage configurations

`milieux config` lets you manage global configurations.

Configs are stored by default in a TOML file, `$HOME/.milieux/config.toml`. If none exists, you will be prompted to create one when running most commands.

The config file stores things like paths to directories containing your environments and distros.

To override the default config path, you can provide `--config` to point to a specific file.

| Subcommand | Description |
| ---------- | ----------- |
| `new`      | Create a new config file |
| `path`     | Print out path to the configs |
| `show`     | Show the configs |

#### PyPI Configurations

`milieux` uses `uv` as its package manager, which in turn defaults to the standard [Python Packaging Index](https://pypi.org/) (PyPI) to download packages. However, you may want to override this in order to use a custom PyPI mirror.

This can be done in one of two ways:

1. Set the `UV_DEFAULT_INDEX` or `UV_INDEX` environment variables.
2. Configure the `default_index` or `indexes` fields in the `[pip]` section of your config file.

Example `pip` section of file:

```toml
[pip]
# URL for default PyPI index
default_index_url = "https://pypi.org/simple"
# URLs for extra indexes, in descending priority order (but all taking priority over the default)
index_urls = [
    "https://internal-pypi-mirror.example.com",
    "https://backup-pypi-mirror.example.com"
]
```

See the `uv` page on [Package Indexes](https://docs.astral.sh/uv/concepts/indexes/) for more information on how package index overrides work.

## Support and feedback

🛠️ Feel free to submit pull requests, ask questions, or make bugfix/feature requests on [Github Issues](https://github.com/jeremander/milieux/issues).
