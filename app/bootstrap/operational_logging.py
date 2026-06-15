from __future__ import annotations

import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path

from flask import Flask, g, request


class RequestContextFilter(logging.Filter):
    """Dosya loglarina request_id ve uzak adres bilgisini ekler."""

    def filter(self, record: logging.LogRecord) -> bool:  # pragma: no cover - log enrichment
        try:
            record.request_id = getattr(g, "request_id", "-")
        except Exception:
            record.request_id = "-"
        try:
            record.remote_addr = request.headers.get("X-Forwarded-For", request.remote_addr or "-").split(",")[0].strip()
        except Exception:
            record.remote_addr = "-"
        return True


def _a11b2_has_rotating_file_handler(logger: logging.Logger, file_path: Path) -> bool:
    """A11B2_RESOURCE_WARNING_FIX: Aynı log dosyası için daha önce handler eklenmiş mi kontrol eder."""
    try:
        target = str(file_path.resolve())
    except Exception:
        target = str(file_path)

    for handler in logger.handlers:
        if not isinstance(handler, RotatingFileHandler):
            continue

        base_filename = getattr(handler, "baseFilename", "") or ""
        try:
            current = str(Path(base_filename).resolve())
        except Exception:
            current = str(base_filename)

        if current == target:
            return True

    return False


def _a11b2_ensure_rotating_file_handler(
    logger: logging.Logger,
    file_path: Path,
    *,
    level: int,
    formatter: logging.Formatter,
    request_filter: logging.Filter,
    max_bytes: int,
    backup_count: int,
) -> None:
    """A11B2_RESOURCE_WARNING_FIX: Handler zaten varsa yeni dosya handler'ı oluşturmaz."""
    if _a11b2_has_rotating_file_handler(logger, file_path):
        return

    handler = RotatingFileHandler(
        file_path,
        maxBytes=max_bytes,
        backupCount=backup_count,
        encoding="utf-8",
        delay=True,
    )
    handler.setLevel(level)
    handler.setFormatter(formatter)
    handler.addFilter(request_filter)
    logger.addHandler(handler)


def configure_operational_logging(app) -> None:
    """Operasyonel loglama handler'larını sızıntı oluşturmadan hazırlar."""
    log_folder = Path(app.config.get("LOG_FOLDER") or "logs")
    log_folder.mkdir(parents=True, exist_ok=True)

    formatter = logging.Formatter(
        "%(asctime)s | %(levelname)s | %(request_id)s | %(remote_addr)s | %(name)s | %(message)s"
    )
    request_filter = RequestContextFilter()

    configured_level_name = str(app.config.get("LOG_LEVEL") or "INFO").strip().upper() or "INFO"
    configured_level = getattr(logging, configured_level_name, logging.INFO)

    app_log_max_bytes = int(app.config.get("APP_LOG_FILE_MAX_BYTES") or 2_000_000)
    app_log_backup_count = int(app.config.get("APP_LOG_BACKUP_COUNT") or 5)
    ops_log_max_bytes = int(app.config.get("OPS_LOG_FILE_MAX_BYTES") or 2_000_000)
    ops_log_backup_count = int(app.config.get("OPS_LOG_BACKUP_COUNT") or 5)

    app_log_path = log_folder / "bys360-app.log"
    ops_log_path = log_folder / "bys360-ops.log"

    _a11b2_ensure_rotating_file_handler(
        app.logger,
        app_log_path,
        level=configured_level,
        formatter=formatter,
        request_filter=request_filter,
        max_bytes=app_log_max_bytes,
        backup_count=app_log_backup_count,
    )
    app.logger.setLevel(configured_level)

    ops_logger = logging.getLogger("bys360.ops")
    ops_logger.setLevel(configured_level)
    ops_logger.propagate = False

    _a11b2_ensure_rotating_file_handler(
        ops_logger,
        ops_log_path,
        level=configured_level,
        formatter=formatter,
        request_filter=request_filter,
        max_bytes=ops_log_max_bytes,
        backup_count=ops_log_backup_count,
    )

    app.extensions["ops_logger"] = ops_logger
