"""JSON logging without external runtime dependencies."""

from __future__ import annotations

import json
import logging
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from aidub.security.redaction import Redactor


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, Any] = {
            "ts": datetime.now(UTC).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": Redactor.text(record.getMessage()),
        }
        fields = getattr(record, "fields", None)
        if isinstance(fields, dict):
            payload.update(Redactor.value(fields))
        if record.exc_info:
            payload["exception"] = Redactor.text(self.formatException(record.exc_info))
        return json.dumps(payload, ensure_ascii=False, separators=(",", ":"))


def configure_logging(
    *,
    level: int = logging.INFO,
    log_file: Path | None = None,
) -> None:
    handlers: list[logging.Handler] = []
    console = logging.StreamHandler(sys.stderr)
    console.setFormatter(JsonFormatter())
    handlers.append(console)

    if log_file is not None:
        log_file.parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(log_file, encoding="utf-8")
        file_handler.setFormatter(JsonFormatter())
        handlers.append(file_handler)

    root = logging.getLogger()
    root.handlers.clear()
    root.setLevel(level)
    for handler in handlers:
        root.addHandler(handler)


class ContextLogger:
    def __init__(self, logger: logging.Logger, context: dict[str, Any] | None = None) -> None:
        self._logger = logger
        self._context = context or {}

    def bind(self, **fields: Any) -> ContextLogger:
        return ContextLogger(self._logger, {**self._context, **fields})

    def _log(self, level: int, message: str, **fields: Any) -> None:
        self._logger.log(
            level,
            message,
            extra={"fields": {**self._context, **fields}},
        )

    def debug(self, message: str, **fields: Any) -> None:
        self._log(logging.DEBUG, message, **fields)

    def info(self, message: str, **fields: Any) -> None:
        self._log(logging.INFO, message, **fields)

    def warning(self, message: str, **fields: Any) -> None:
        self._log(logging.WARNING, message, **fields)

    def error(self, message: str, **fields: Any) -> None:
        self._log(logging.ERROR, message, **fields)

    def exception(self, message: str, **fields: Any) -> None:
        self._logger.error(
            message,
            exc_info=True,  # noqa: LOG014 - public helper is called from exception handlers
            extra={"fields": {**self._context, **fields}},
        )


def get_logger(name: str, **context: Any) -> ContextLogger:
    return ContextLogger(logging.getLogger(name), context)
