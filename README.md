# Fallout RPG

**A web-based companion for running tabletop adventures in the Fallout wasteland.**

Fallout RPG brings campaign management, character sheets and game mechanics
together in one place. It helps gamemasters keep track of the world and its
inhabitants, resolve encounters and follow the consequences of play — leaving
more room at the table for exploration, difficult choices and questionable loot.

The project implements a **homebrew game system**, built around S.P.E.C.I.A.L.
and a personal interpretation of the Fallout universe. It is not a direct
implementation of J. Sawyer's Fallout PnP rules: combat, progression and other
mechanics have been adapted to suit this system's approach to gameplay.

Originally built for a personal table, it has grown into a Django application
with a tested rules engine, a REST API, French and English translations, and
documented packaging and deployment options. It remains an independent project
rather than an official Fallout product.

## Features

- **Campaign management** — track in-game time, turn order, radiation levels,
  campaign-wide effects and loot.
- **Characters and creatures** — manage S.P.E.C.I.A.L., skills, derived
  statistics, progression, health and action points.
- **Combat resolution** — handle single shots, targeted attacks and bursts,
  armor protection, damage, healing and critical hits.
- **Inventory and equipment** — maintain weapons, armor, ammunition and
  consumables, including reloading, durability and repairs.
- **Effects and survival** — apply bonuses, penalties, perks, traits and
  ongoing effects, with mechanics for needs and radiation.
- **Rolls and history** — resolve skill checks and keep a record of rolls and
  combat outcomes.
- **Item catalogues and loot** — use the bundled item and creature fixtures
  and generate random loot.

## Project status

The application and its homebrew rules continue to evolve. Automated tests cover
the rules engine, API transactions and access permissions, alongside deployment
initialization. Compatibility across releases is not guaranteed, particularly
when the rules or database schema change: back up campaign data and test upgrades
on a separate instance before updating a running game.

## Installation and deployment

Choose Docker Compose for a containerized setup, Ansible for a native server
installation, or a Python environment for local development.

### Docker Compose

The production-oriented Compose stack includes Gunicorn, a Celery worker,
PostgreSQL, Redis and Nginx for static files. Copy `.env.example` to `.env`,
fill in the secrets and HTTPS domain settings, then run:

```bash
docker compose up --build -d
```

On a new database, initialization migrates, imports `admin`, `items` and
`creatures`, replaces the fixture admin password with `FALLOUT_ADMIN_PASSWORD`,
and collects static files. Existing users prevent fixture replay.
There is no default production password.

The HTTP listener is bound to `127.0.0.1:8080` and requires a trusted HTTPS
reverse proxy in front of it. See [DOCKER.md](DOCKER.md) for deployment,
persistence, upgrades and media access limitations.

### Native deployment with Ansible

For a native systemd deployment with PostgreSQL, Redis, Celery and Nginx HTTPS
(Let's Encrypt), see [ansible/README.md](ansible/README.md).

### Local development

Install the dependencies in a dedicated virtual environment with
`python -m pip install -r requirements.txt`. Django's development server can
then be started with `python manage.py runserver`.

### From an installed package

The `fallout-rpg` distribution includes both the `fallout` Django application and
the `rpg` project, migrations, fixtures, source static assets, templates and
compiled French/English translations. It requires Python 3.13 or newer.

After publication, install it in a dedicated environment:

```bash
python -m pip install fallout-rpg
mkdir fallout-instance
cd fallout-instance
export FALLOUT_HOME="$PWD"
export DJANGO_CONFIGURATION=Test
export DJANGO_SECRET_KEY="$(python -c 'import secrets; print(secrets.token_urlsafe(64))')"
fallout-rpg migrate
fallout-rpg createsuperuser
fallout-rpg collectstatic --noinput
fallout-rpg runserver 127.0.0.1:8000
```

Keep the same secret key between restarts. `Test` and `runserver` are for local
development only. The package does not create accounts, migrate a database or
load fixtures on installation. In particular, it does not load the example
`admin` fixture automatically.

Installed-package data defaults to the current working directory, or to
`FALLOUT_HOME` when set. This includes the default SQLite database, collected
static files and uploaded media; bundled resources stay inside the package.
`DATABASE_URL` can select another database. The `postgresql` extra installs the
PostgreSQL driver: `python -m pip install 'fallout-rpg[postgresql]'`.

For production, configure `DJANGO_CONFIGURATION=Prod`, a stable
`DJANGO_SECRET_KEY`, the database and Redis, then use a WSGI server with
`rpg.wsgi:application`. Serve collected static files and uploaded media
separately. See [PACKAGING.md](PACKAGING.md) for build and release instructions.

## Feedback and contributions

Bug reports, suggestions and feedback from your own games are welcome. Open an
issue to describe a problem or discuss an idea; for rules-related changes,
please explain the gameplay intent as well as the proposed implementation.

## License

The original code and documentation are available under the [MIT license](LICENSE).
Fallout-related artwork, trademarks and bundled third-party libraries are not
relicensed under MIT; see [NOTICE](NOTICE) and their original notices. Check the
rights applicable to game assets before redistributing the complete package.
