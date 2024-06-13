<!-- markdownlint-disable MD034 -->

# TODO

## v0.2.1

- Switch to `rich` for prompts, tables, etc.

## Future

- Subcommands
    - Build/publish
        - May just be thin wrappers for `hatch`?
        - Or could build wheels for entire distro and upload them all
            - `uv` does not yet seem to replace `pip wheel`
        - `build`
            - Build `sdist` or `wheel`
            - See: https://pip.pypa.io/en/stable/cli/pip_wheel/
        - `publish`
            - Publish to PyPI (actual or local)
    - `config`
        - Config registry: various pre-made configs stored within `milieux`?
        - `use`: use a pre-installed config
            - Can give a path and it will copy it to user location
            - Otherwise, shows list and prompts to view each one
                - Once viewed, prompts whether to use
    - `env`
        - `create`
            - "Stock" environments (testing, linting, etc.) with names
                - can roll current `--seed` into this (e.g. `--seed default`)
        - `list`
            - Perhaps display owner and creation time (human-readable)
    - `test`
        - Run `pytest` on all projects in a distro
    - `metrics`
        - Compute source metrics for a distro
    - `deps`
        - Analyze dependency graph
    - `docs`
        - `sphinx` or `mkdocs`
        - Build a single site, or multiple sites for each project
    - `scaffold`
        - Support `cookiecutter` or some means of custom scaffolding
        - Interactive `-i` flag
        - `poetry` scaffolder?
            - Gracefully handle missing utility.
        - Extra dep. group `[scaffold]`, perhaps?
- Quiet/verbose mode for `uv` subcommands
- "Recipes" (in README)
    - create dev environment
    - activate/use dev environment (including someone else's)
    - build full distro (configure PyPI mirror first)
        - include module file for end users
    - create a new distro (optionally, atop a base distro)
    - run tests for a whole distro
    - get source metrics for a whole distro
