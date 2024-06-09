# Milieux

[![PyPI - Version](https://img.shields.io/pypi/v/milieux)](https://pypi.org/project/milieux)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://raw.githubusercontent.com/jeremander/daikanban/main/LICENSE)
[![pre-commit](https://img.shields.io/badge/pre--commit-enabled-brightgreen?logo=pre-commit)](https://github.com/pre-commit/pre-commit)

A general-purpose tool to assist in developing, building, and installing Python packages.

## Introduction

`milieux` is a tool used for managing multiple [virtual environments](https://realpython.com/python-virtual-environments-a-primer/#why-do-you-need-virtual-environments) and *distributions*.

We define a *distribution* (or "distro") to be a collection of Python packages you often want bundled together. For example, you might want to bundle `numpy`, `scipy`, and `pandas` together into a distribution named `scientific`, which you can then install into one more more virtual environments. To do this, you can run:

```shell
milieux distro new scientific -p numpy scipy pandas
```

Then to create a new environment `my_project` and install all dependencies from this distribution:

```shell
milieux env new my_project

milieux env install -d scientific
```

✨ Dependencies and environments are managed by the [uv](https://github.com/astral-sh/uv) tool, an ultra-fast package installer and resolver.

## Installation

```shell
pip install milieux
```

## Usage

View help menu:

```shell
milieux -h
```

View subcommand help menu:

```shell
milieux <SUBCOMMAND> -h
```

For brevity, you may want to alias the command as follows:

```shell
alias mlx="milieux"
```

Then you can type `mlx` in place of the full (tricky-to-spell) name.

## Commands

Here is a quick tour of the commands available in `milieux`.

### Scaffold

`milieux scaffold` creates a new Python project from a default or custom scaffold.

```shell
milieux scaffold my_project
```

The command above will create a new project in a `my_project` subdirectory.

The `--utility` argument lets you specify the utility for creating the project scaffold.

🚧 At present, the only supported scaffold utility is [hatch](https://hatch.pypa.io/latest). In the future we plan to support arbitrary project templates via [jinja2](https://jinja.palletsprojects.com/en/3.1.x/) and/or [cookiecutter](https://cookiecutter.readthedocs.io/en/stable/).

### Configuration

`milieux config` lets you manage global configurations.

Configs are stored by default in a TOML file, `$HOME/.milieux/config.toml`. If none exists, you will be prompted to create one when running most commands.

The config file stores things like paths to directories containing your environments and distros.

To override the default config path, you can provide `--config` to point to a specific file.

| Subcommand | Description |
| ---------- | ----------- |
| `new`      | Create a new config file |
| `path`     | Print out path to the configs |
| `show`     | Show the configs |

## Support and feedback

🛠️ Feel free to submit pull requests, ask questions, or make bugfix/feature requests on [Github Issues](https://github.com/jeremander/milieux/issues).
