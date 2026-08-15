"""Atomic settings persistence."""

from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path

from .settings import ApplicationSettings


class SettingsRepository:
    def __init__(self, path: Path | str) -> None:
        self.path = Path(path).expanduser()
        if not self.path.is_absolute():
            raise ValueError("settings path must be absolute")

    def load(self) -> ApplicationSettings:
        if not self.path.exists():
            return ApplicationSettings()
        if not self.path.is_file():
            raise OSError(f"settings path is not a file: {self.path}")
        with self.path.open("r", encoding="utf-8") as stream:
            payload = json.load(stream)
        return ApplicationSettings.model_validate(payload)

    def save(self, settings: ApplicationSettings) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        descriptor, temporary_name = tempfile.mkstemp(
            prefix=f".{self.path.name}.",
            suffix=".tmp",
            dir=self.path.parent,
        )
        temporary = Path(temporary_name)
        try:
            with os.fdopen(descriptor, "w", encoding="utf-8", newline="\n") as stream:
                json.dump(
                    settings.model_dump(mode="json"),
                    stream,
                    ensure_ascii=False,
                    indent=2,
                    sort_keys=True,
                )
                stream.write("\n")
                stream.flush()
                os.fsync(stream.fileno())
            temporary.replace(self.path)
        except BaseException:
            temporary.unlink(missing_ok=True)
            raise
