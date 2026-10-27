# Building and publishing Fallout RPG

## Distribution

- PyPI distribution: `fallout-rpg`.
- Python packages: `fallout` (Django application), `rpg` (complete project).
- Management command: `fallout-rpg`, equivalent to the project's `manage.py`.
- Version: the literal `__version__` in `rpg/__init__.py`. Hatch reads it without
  importing Django or the Celery application during the build.
- License: MIT for original code/documentation, with third-party exclusions in
  `NOTICE`. This does not establish redistribution rights for game artwork.

`pyproject.toml` declares runtime dependencies and the `dev` / `postgresql`
extras. `requirements.txt` retains the existing pinned development/deployment
environment; it is not used as package metadata, since it also includes tools.

## Build

Use a dedicated Python 3.13+ environment:

```bash
python -m pip install '.[dev]'
python -m pytest
python -m build
python -m twine check dist/fallout_rpg-2026.10.27*
```

Hatchling builds an sdist, then a wheel from that sdist. The isolated build
environment installs Hatchling and Babel. `hatch_build.py` validates and compiles
the `.po` files into `.mo` files using Babel; GNU gettext and configured Django
settings are not required to build the package.

The wheel contains the application's migrations, management commands, fixtures,
templates, assets and translations. Shared project assets/templates/locales are
mapped into `rpg/statics`, `rpg/templates` and `rpg/locale`. The sdist also contains
tests, management script and source build configuration.

An explicit allowlist excludes local databases, uploaded media, collected
`static/`, logs, dotenv files, caches, IDE configuration and local audit notes.
Only `fallout/static/` and `statics/` are static asset sources. Existing compiled
catalogs are ignored and freshly generated ones are included during each build.

## Installation smoke test

Install the wheel into a fresh environment and run it outside the checkout:

```bash
python -m venv /path/to/test-venv
/path/to/test-venv/bin/python -m pip install dist/fallout_rpg-2026.10.27-py3-none-any.whl
mkdir /path/to/empty-instance
cd /path/to/empty-instance
export FALLOUT_HOME="$PWD"
export DJANGO_CONFIGURATION=Test
export DJANGO_SECRET_KEY=local-package-verification-only
export DATABASE_URL=sqlite:///:memory:
/path/to/test-venv/bin/fallout-rpg check
/path/to/test-venv/bin/fallout-rpg findstatic fallout/js/script.js js/jquery.min.js
```

Check that the wheel imports from the fresh environment, not an editable
checkout; that templates and French/English catalogs are available; and that
no instance files are written into `site-packages`. Never use an existing
application database for a packaging check. Installing a wheel must not run
migrations or load fixtures.

## Publication

Local validation on 27 October 2026: isolated build without Django configuration,
successful `twine check`, 559 passing tests (241 subtests), wheel installation
with dependencies into a fresh environment, and successful `pip check`.
From an instance outside the checkout: Django `check`, static/template lookup,
French/English translations and writable data/log paths were verified.

The complete archives measure approximately **116.6 MiB for the sdist** and
**118.4 MiB for the wheel**, exceeding the usual 100 MiB limit.
Nothing has been uploaded.

Review archive contents, dependencies, licenses, rights to third-party assets
and artifact sizes before uploading. PyPI commonly limits each file to 100 MiB;
the artwork may require a project-specific file-size limit increase. Do not
silently omit artwork or change it just to fit that limit.

```bash
python -m twine upload --repository testpypi dist/fallout_rpg-2026.10.27*
python -m twine upload --repository pypi dist/fallout_rpg-2026.10.27*
```

Use repository-scoped API tokens via Twine's prompt, keyring or environment;
never put tokens in project files. PyPI release filenames cannot be overwritten:
increase `rpg.__version__` before publishing changed artifacts. Adapt the artifact
version in the commands above at the same time.
