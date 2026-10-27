# Fallout RPG

This project aims to provide tools to a Fallout RPG (or Pen & Paper) gamemaster.

The game system is **not** a copy of the Fallout PnP by J. Sawyer, I changed many things 
I found very odd and which can broke the gameplay and/or the immersion. 
View this as my own and personal interpretation of the Fallout game system.

By the way, I'm still working of this system and I don't really care about the
retro-compatibility with existing or running projects (especially with database migrations),
so don't be surprised if a newer versions does not work above an older one.

Currenty the project includes:

* Campaigns
  * Time management
  * Loot management
  * Global effects
  * Radiation level
  * Turn sequence
* Characters and creatures
  * Primary and derived statistics
  * Health and actions
  * Single, targetted ou burst attacks
  * Damage management
  * Inventory and equipment management
  * Effects (malus, bonus, perks, traits)
  * S.P.E.C.I.A.L. and skills rolls
  * Rolls and fight history
* Items management (weapons, armors, consumables)
* Random loots

## How to use it?

#### With docker

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

#### From Python

For a native systemd deployment with PostgreSQL, Redis, Celery and Nginx HTTPS
(Let's Encrypt), see [ansible/README.md](ansible/README.md).

Like any Django project, you can start a development webserver with this command line:

`python manage.py runserver`

You have to install the requirements first with: `pip install -r requirements.txt`.
Don't hesitate to install them in a dedicated virtualenv.

#### From an installed package

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

## Any questions?

Feel free to provide any feedback or anomalies through an issue or an email.

## License

The original code and documentation are available under the [MIT license](LICENSE).
Fallout-related artwork, trademarks and bundled third-party libraries are not
relicensed under MIT; see [NOTICE](NOTICE) and their original notices. Check the
rights applicable to game assets before redistributing the complete package.
