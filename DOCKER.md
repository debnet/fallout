# Production-oriented Docker deployment

## Prepare

Use Docker Engine and modern Docker Compose. Copy `.env.example` to `.env` and
restrict its permissions (`chmod 600 .env`). Fill in:

- `DJANGO_SECRET_KEY`: a long, unique random secret, stable across restarts.
- `POSTGRES_PASSWORD`: a separate random URL-safe password (no `@`, `/`, `:` or
  other URL delimiters, since it is interpolated into `DATABASE_URL`).
- `FALLOUT_ADMIN_PASSWORD`: a strong initial password for `admin`, validated
  using Django's production password validators.
- `DJANGO_ALLOWED_HOSTS`: comma-separated host names, without schemes or `*`.
- `DJANGO_CSRF_TRUSTED_ORIGINS`: comma-separated HTTPS origins.

Generate secrets independently with
`python -c 'import secrets; print(secrets.token_urlsafe(48))'`.
Secrets are passed at runtime, never baked into the image. `.env` is ignored by
Git and excluded from the Docker build context. For managed deployment, use
your platform's secret injection instead; environment variables remain visible
to Docker administrators.

```bash
docker compose config --quiet
docker compose up --build -d
docker compose logs setup web worker
```

Do not print or share `docker compose config` output without `--quiet`: it can
contain expanded secrets.

## HTTPS and networking

Only Nginx is published, on `127.0.0.1:8080` (override `HTTP_PORT` if needed).
PostgreSQL, Redis and Gunicorn have no host-published ports. Put a trusted TLS
terminator on the same host in front of this listener, forwarding the original
Host header. Configure its public hostname in the variables above.

The internal Nginx listener marks proxied requests as HTTPS. This is intentional:
it must receive traffic only from the trusted TLS terminator, not directly from
the Internet. Production HTTPS redirects and secure cookies stay enabled.
Direct browser access over HTTP is not a supported deployment mode.

Nginx serves collected `/static/` files. `/medias/` is deliberately denied:
uploads may be private, and publishing the whole directory would bypass access
controls. Uploaded files persist, but production delivery requires a separately
designed authenticated serving mechanism (or an explicit decision that selected
files are public). No public media directory is enabled implicitly.

## Initialization and persistence

`setup` waits for healthy PostgreSQL/Redis, runs migrations, `bootstrap`, then
`collectstatic`. Web and worker wait for its successful completion. A fixture or
migration failure stops startup rather than starting a partially initialized app.

`bootstrap` imports `admin`, `items` and `creatures` together in a transaction on
a database without users, replacing the fixture password before commit. If any
user already exists, it skips **all** fixtures and does not reset passwords or
overwrite gameplay data. Use it only for a fresh installation; it is not a
repair/update mechanism for an existing catalogue. Run only one initializer per
database at a time. Import errors roll back all fixture changes.
An existing item/character catalogue without users is rejected rather than
overwritten.

Remove `FALLOUT_ADMIN_PASSWORD` from `.env` after a successful first boot, then
recreate `setup` to remove it from the old container's environment. Recover or
rotate passwords explicitly with `docker compose run --rm web fallout-rpg
changepassword admin`; never replay the admin fixture on a running database.

Named volumes:

- `pgdata`: PostgreSQL 17 data.
- `redisdata`: Redis AOF persistence (broker, results and cache use separate DBs).
- `appdata`: uploaded media, collected static files and instance files.

`docker compose down` keeps volumes. **`down -v` destroys application data.**
Back up PostgreSQL and uploaded media, and test restores. Redis persistence is
not a guarantee of exactly-once task delivery. Monitor memory/disk usage: Redis
uses `noeviction` to avoid silently evicting queued tasks. PostgreSQL/Redis are
trusted internal services, not authenticated public endpoints; do not attach
untrusted containers to their network.

## Runtime and upgrades

The multi-stage build installs the wheel, PostgreSQL binary driver and Gunicorn
without development dependencies. Runtime app processes run as UID/GID 10001,
without Linux capabilities. Celery accepts JSON only, not executable pickle
payloads. Stdout/stderr contain web and worker logs.

Before an upgrade, back up the database/media and stop writers:

```bash
docker compose stop proxy web worker
docker compose build
docker compose run --rm setup
docker compose up -d --force-recreate
```

Keep database major-version upgrades separate; changing the image tag does not
migrate an existing PostgreSQL data directory. Image tags pin major/minor release
lines, not immutable digests; pin reviewed digests and lock dependency versions
for reproducible releases. Set log rotation, resource limits, monitoring and
backup retention according to your host capacity. No scheduler is started because
this project currently defines no periodic Celery schedule.

Do not reuse previously queued pickle tasks with the JSON-only worker: drain
them with the old trusted worker before upgrading (never enable pickle for
untrusted broker contents).
