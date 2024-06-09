# Milieux

[![PyPI - Version](https://img.shields.io/pypi/v/milieux)](https://pypi.org/project/milieux)
![GitHub Actions Workflow Status](https://img.shields.io/github/actions/workflow/status/jeremander/milieux/workflow.yml)
![Coverage Status](https://github.com/jeremander/milieux/raw/coverage-badge/coverage-badge.svg)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://raw.githubusercontent.com/jeremander/milieux/main/LICENSE)
[![pre-commit](https://img.shields.io/badge/pre--commit-enabled-brightgreen?logo=pre-commit)](https://github.com/pre-commit/pre-commit)

A general-purpose tool to assist in developing, building, and installing Python packages.

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

- 🧘 [loguru](https://loguru.readthedocs.io/en/stable/), for logging output.

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

```shell
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

#### Sync packages

`milieux env sync` is similar to `install`, but instead of installing new packages, it will *sync* them to the environment, making sure these are the *only* packages in the environment. This is ideal for controlling exactly what version of each specific package you want (see: [locking dependencies](#locking-dependencies)).

### `scaffold`: Create project scaffold

`milieux scaffold` creates a new Python project from a default or custom scaffold.

```shell
milieux scaffold my_project
```

The command above will create a new project in a `my_project` subdirectory.

The `--utility` argument lets you specify the utility for creating the project scaffold.

🚧 At present, the only supported scaffold utility is [hatch](https://hatch.pypa.io/latest). In the future we plan to support arbitrary project templates via [jinja2](https://jinja.palletsprojects.com/en/3.1.x/) and/or [cookiecutter](https://cookiecutter.readthedocs.io/en/stable/).

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

## Support and feedback

🛠️ Feel free to submit pull requests, ask questions, or make bugfix/feature requests on [Github Issues](https://github.com/jeremander/milieux/issues).
