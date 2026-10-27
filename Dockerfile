FROM python:3.13-slim-bookworm AS builder

ENV PIP_DISABLE_PIP_VERSION_CHECK=1
WORKDIR /build
RUN python -m pip install --no-cache-dir 'build>=1.2,<2'
COPY pyproject.toml hatch_build.py fallout_cli.py README.md LICENSE NOTICE ./
COPY fallout/ fallout/
COPY rpg/ rpg/
COPY statics/ statics/
COPY templates/ templates/
COPY locale/ locale/
RUN python -m build --wheel --outdir /wheels
RUN python -m pip wheel --wheel-dir /wheels '/wheels/'*.whl 'psycopg[binary]>=3.3.2,<4' 'gunicorn>=23,<28'

FROM python:3.13-slim-bookworm AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    DJANGO_SETTINGS_MODULE=rpg.settings \
    DJANGO_CONFIGURATION=Prod \
    FALLOUT_HOME=/var/lib/fallout

RUN groupadd --gid 10001 fallout \
    && useradd --uid 10001 --gid fallout --create-home fallout \
    && mkdir -p /var/lib/fallout/static /var/lib/fallout/medias \
    && chown -R fallout:fallout /var/lib/fallout
COPY --from=builder /wheels /wheels
RUN python -m pip install --no-cache-dir --no-index --find-links=/wheels \
        'fallout-rpg[postgresql]' 'gunicorn>=23,<28' \
    && rm -r /wheels
USER fallout
WORKDIR /var/lib/fallout
EXPOSE 8000
CMD ["gunicorn", "rpg.wsgi:application", "--bind=0.0.0.0:8000", "--workers=3", "--timeout=60", "--access-logfile=-", "--error-logfile=-", "--worker-tmp-dir=/tmp"]
