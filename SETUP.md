# Installing and publishing CodePilot

## Requirements

- Python 3.14 or newer (as specified by `pyproject.toml`).
- An OpenAI API key for model requests.

## Install as a user

After CodePilot has been published to PyPI, install it with pip:

```console
pipx install codepilot
```

`pipx` installs command-line applications in an isolated environment and
exposes the `codepilot` command. Alternatively, use `python -m pip install
codepilot` in a virtual environment and ensure its scripts directory is on
`PATH`.

Then configure the key and launch the CLI:

```console
codepilot setup
codepilot chat
```

`codepilot setup` prompts for the key without echoing it, asks for confirmation,
and writes it to a per-user `.env` file:

- Linux/macOS: `$XDG_CONFIG_HOME/codepilot/.env`, or
  `~/.config/codepilot/.env` when `XDG_CONFIG_HOME` is not set.
- Windows: `%APPDATA%/codepilot/.env`.

The file is created with owner-only permissions where the operating system
supports Unix file permissions. Running `codepilot setup` again replaces the
saved key. The key is not printed to the terminal.

For CI, containers, or users who manage secrets themselves, the
`OPENAI_API_KEY` environment variable takes precedence. Otherwise, the saved
per-user key takes precedence over a project-local `.env`; that file is still
supported as a development fallback. Do not commit either file or publish API
keys.

Package installers should not prompt for secrets: installs are often automated,
run without a terminal, and should not require credentials just to install the
program. Users configure credentials explicitly with `codepilot setup` after
installation.

## Test locally

From the repository root:

```console
uv sync
uv run pytest
uv run codepilot --help
uv run codepilot setup
```

`uv run codepilot setup` writes to the user's configuration directory. Use a
throwaway OpenAI API key if you run it during development.

## Build and inspect distribution files

Install `uv`, then build both source and wheel distributions:

```console
uv build
```

The distributions are written to `dist/`. Check that both files contain the
package metadata and expected source before uploading:

```console
uv run --with twine twine check dist/*
```

The distribution name is set by `project.name` in `pyproject.toml`. PyPI names
must be unique; if `codepilot` is unavailable, choose an available name and
update `project.name` before publishing. The installed command name is
controlled separately by `[project.scripts]`.

## Publish to TestPyPI first

1. Create a TestPyPI account and create a project-scoped API token.
2. Build the distributions with `uv build`.
3. Publish using the token in an environment variable:

   ```console
   export UV_PUBLISH_TOKEN='pypi-your-test-token'
   uv publish --publish-url https://test.pypi.org/legacy/
   ```

4. In a clean virtual environment, install from TestPyPI and exercise the
   installed command:

   ```console
   python -m venv /tmp/codepilot-test
   /tmp/codepilot-test/bin/python -m pip install \
     --index-url https://test.pypi.org/simple/ codepilot
   /tmp/codepilot-test/bin/codepilot --help
   ```

TestPyPI does not mirror all dependencies from PyPI. If installation reports a
missing dependency, use PyPI as the extra package index:

```console
/tmp/codepilot-test/bin/python -m pip install \
  --index-url https://test.pypi.org/simple/ \
  --extra-index-url https://pypi.org/simple/ codepilot
```

## Publish to PyPI

1. Create and verify a PyPI account, enable two-factor authentication, and
   create a project-scoped API token.
2. Set the token and publish the already-tested build:

   ```console
   export UV_PUBLISH_TOKEN='pypi-your-production-token'
   uv publish
   ```

3. Install from PyPI in a clean environment and verify the public CLI:

   ```console
   python -m pip install codepilot
   codepilot --help
   codepilot setup
   ```

Never commit a publishing token. For automated publishing, prefer PyPI Trusted
Publishers (OIDC) over storing a long-lived token in repository secrets.

## Release checklist

- Bump `project.version` in `pyproject.toml`; published versions cannot be
  reused.
- Confirm the package name, Python requirement, README, and project URLs.
- Run `uv run pytest` and `uv build`.
- Inspect `dist/` and run `twine check`.
- Test installation and the `codepilot` entry point on TestPyPI.
- Publish to PyPI and verify installation in a clean environment.
- Do not include `.env`, API keys, local virtual environments, or generated
  project output in the distribution.
