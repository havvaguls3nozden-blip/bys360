from __future__ import annotations

from urllib.parse import urlparse
import socket

DOCKER_REDIS_HOSTS = {"redis", "cache", "valkey"}
PROD_LIKE_ENVS = {"production", "staging", "pilot", "live", "canli", "canlı"}


def is_docker_hostname_url(url: str | None) -> bool:
    if not url:
        return False
    try:
        host = (urlparse(str(url)).hostname or "").strip().lower()
    except Exception:
        import logging
        logging.getLogger(__name__).exception("BYS360 SAFE V6: sessiz yakalanan hata loglandi.")
        return False
    return host in DOCKER_REDIS_HOSTS


def can_resolve_redis_url(url: str | None) -> bool:
    if not url:
        return False
    try:
        host = urlparse(str(url)).hostname
        if not host:
            return False
        socket.getaddrinfo(host, None)
        return True
    except Exception:
        import logging
        logging.getLogger(__name__).exception("BYS360 SAFE V6: sessiz yakalanan hata loglandi.")
        return False


def sanitize_redis_url(raw_url: str | None, *, app_env: str, deployment_mode: str = "") -> tuple[str, str | None]:
    url = (raw_url or "").strip()
    if not url:
        return "", None
    env = (app_env or "").strip().lower()
    mode = (deployment_mode or "").strip().lower()
    if (
        is_docker_hostname_url(url)
        and env in PROD_LIKE_ENVS
        and mode not in {"docker", "compose", "container"}
        and not can_resolve_redis_url(url)
    ):
        return "", "redis_url_docker_hostname_unresolved"
    return url, None
