# BYS360_OPS_HARDENING_V1
# Flask / Python 3.12 production container image.
# Secrets are not copied into the image; provide them through environment variables
# or a server-side env file that is never committed.

FROM python:3.12-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PORT=8000 \
    BYS360_DEPLOYMENT_MODE=docker

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends curl ca-certificates libpq5 \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt /app/requirements.txt
RUN python -m pip install --upgrade pip setuptools wheel \
    && python -m pip install -r /app/requirements.txt

COPY . /app

RUN chmod +x /app/docker/entrypoint.sh \
    && adduser --disabled-password --gecos "" --uid 10001 bys360 \
    && mkdir -p /app/logs /app/reports /app/instance \
    && chown -R bys360:bys360 /app

USER bys360

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=45s --retries=3 \
    CMD curl -fsS "http://127.0.0.1:${PORT}/health" || curl -fsS "http://127.0.0.1:${PORT}/healthz" || exit 1

ENTRYPOINT ["/app/docker/entrypoint.sh"]
CMD ["gunicorn", "--config", "docker/gunicorn.conf.py", "wsgi:app"]
