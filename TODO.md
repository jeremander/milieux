<!-- markdownlint-disable MD034 -->

# TODO

## v0.1.0

- Rudimentary `README`

## v0.2.0

- Editable installs
- Some mechanism for "hooks" or "templates" to create arbitrary scaffold (file or directory tree) when creating a new environment, using jinja2 and variables like `ENV_NAME`, `ENV_DIR`.
    - Can pass a file/directory path to `env create`, or have separate command `env hook`
- Subcommands
    - `build`
        - Build `sdist` or `wheel`
        - Should it be a single project or an entire distribution?
    - `publish`
        - publish to PyPI (actual or local)

## v0.3.0

- Switch to `rich` for prompts, tables, etc.
- Gracefully catch `KeyboardInterrupt` in prompts
- Quiet/verbose mode for `uv` subcommands
- "Recipes" (in README)
    - create dev environment
    - activate/use dev environment (including someone else's)
    - build full distro (configure PyPI mirror first)
        - include module file for end users
    - create a new distro (optionally, atop a base distro)
    - run tests for a whole distro
    - get source metrics for a whole distro

## Future

- Subcommands
    - `config`
        - Config registry: various pre-made configs stored within `milieux`?
        - `use`: use a pre-installed config
            - Can give a path and it will copy it to user location
            - Otherwise, shows list and prompts to view each one
                - Once viewed, prompts whether to use
    - `env`
        - `create`
            - Option to specify a base environment (via `uv pip freeze`)
            - Or "stock" environments (testing, linting, etc.) with names
                - can roll current `--seed` into this (e.g. `--seed default`)
        - `list`
            - Perhaps display owner and creation time (human-readable)
    - `test`
        - run `pytest` on all projects in a distro
    - `metrics`
        - compute source metrics for a distro
    - `docs`
        - `sphinx` or `mkdocs`
        - Build a single site, or multiple sites for each project
    - `scaffold`
        - Use `poetry`, `cookiecutter`, etc.
