<!-- markdownlint-disable MD034 -->

# TODO

- Newlines in function signatures? Default width?
- Allow comments in requirements files
```python
try:
    lines = read_lines(req)
except ... as e:
    raise NoSuch...
for line in lines:
    line = line.strip()
    if (not line) or line.startswith('#'):  # ignore comments
        continue
    pkgs.add(line)
```
- Accept distribution name *or* import name, e.g.
```python
import importlib.metadata
importlib.metadata.distribution('beautifulsoup4').files
```
    Then find packages among the list of files.
- List all packages in top-level navbar (avoid the one layer of nesting).
- Non-strict mode for missing packages in list?


---

- Subcommands
    - Build/publish
        - May just be thin wrappers for `uv build`?
        - Or could build wheels for entire distro and upload them all
            - use `pip wheel -r <distro>` to do this
            - `uv` does not yet seem to replace `pip wheel`
                - See: https://github.com/astral-sh/uv/issues/1681
        - `build`
            - Build `sdist` or `wheel`
            - See: https://pip.pypa.io/en/stable/cli/pip_wheel/
        - `publish`
            - Publish to PyPI (actual or local)
    - `config`
        - Switch to `pydantic` `BaseSettings` to get validation?
        - Config registry: various pre-made configs stored within `milieux`?
        - `use`: use a pre-installed config
            - Can give a path and it will copy it to user location
            - Otherwise, shows list and prompts to view each one
                - Once viewed, prompts whether to use
    - `doc`
        - Get `pydantic.dataclass` fields to work properly.
        - Improve default landing page via `index.md.jinja`?
        - Enable package-specific customization, e.g. different docstring styles.
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
    - `scaffold`
        - Support `cookiecutter` or some means of custom scaffolding
        - Interactive `-i` flag
        - `poetry` scaffolder?
            - Gracefully handle missing utility.
        - Extra dep. group `[scaffold]`, perhaps?
- Quiet/verbose mode for `uv` subcommands
- Tab completion?
- "Recipes" (in README)
    - create dev environment
    - activate/use dev environment (including someone else's)
    - build full distro (configure PyPI mirror first)
        - include module file for end users
    - create a new distro (optionally, atop a base distro)
    - run tests for a whole distro
    - get source metrics for a whole distro
