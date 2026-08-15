"""Deterministic discovery and application of project schema migrations."""

from __future__ import annotations

import hashlib
import re
import sqlite3
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Iterable, Iterator

from .errors import MigrationError, MigrationIntegrityError, NewerSchemaError
from .models import MigrationInfo, MigrationReport, utc_now

_MIGRATION_NAME = re.compile(r"^(?P<version>[0-9]{4,})_(?P<name>[a-z][a-z0-9_]*)\.sql$")


@dataclass(frozen=True, slots=True)
class Migration:
    version: int
    name: str
    sql: str
    checksum: str
    source: Path


def default_migrations_directory() -> Path:
    """Locate migrations bundled inside the installable Python package."""

    return Path(__file__).resolve().with_name("migrations_sql")


def discover_migrations(directory: Path | str | None = None) -> tuple[Migration, ...]:
    migration_dir = Path(directory) if directory is not None else default_migrations_directory()
    if not migration_dir.is_dir():
        raise MigrationError(f"migration directory does not exist: {migration_dir}")

    discovered: list[Migration] = []
    for path in sorted(migration_dir.iterdir(), key=lambda item: item.name):
        if not path.is_file():
            continue
        match = _MIGRATION_NAME.fullmatch(path.name)
        if match is None:
            if path.suffix.lower() == ".sql":
                raise MigrationError(f"invalid migration filename: {path.name}")
            continue
        raw = path.read_bytes()
        try:
            sql = raw.decode("utf-8")
        except UnicodeDecodeError as exc:
            raise MigrationError(f"migration is not UTF-8: {path}") from exc
        discovered.append(
            Migration(
                version=int(match.group("version")),
                name=match.group("name"),
                sql=sql,
                checksum=hashlib.sha256(raw).hexdigest(),
                source=path,
            )
        )

    if not discovered:
        raise MigrationError(f"no migrations found in {migration_dir}")
    versions = [migration.version for migration in discovered]
    if len(versions) != len(set(versions)):
        raise MigrationError("duplicate migration version")
    expected = list(range(1, versions[-1] + 1))
    if versions != expected:
        raise MigrationError(f"migration versions must be contiguous: found {versions}")
    return tuple(discovered)


def latest_supported_version(directory: Path | str | None = None) -> int:
    return discover_migrations(directory)[-1].version


def _schema_version_exists(connection: sqlite3.Connection) -> bool:
    row = connection.execute(
        "SELECT 1 FROM sqlite_schema WHERE type = 'table' AND name = 'schema_version'"
    ).fetchone()
    return row is not None


def read_migration_history(connection: sqlite3.Connection) -> tuple[MigrationInfo, ...]:
    if not _schema_version_exists(connection):
        return ()
    rows = connection.execute(
        "SELECT version, name, checksum, applied_at FROM schema_version ORDER BY version"
    ).fetchall()
    return tuple(
        MigrationInfo(
            version=int(row[0]),
            name=str(row[1]),
            checksum=str(row[2]),
            applied_at=str(row[3]),
        )
        for row in rows
    )


def current_schema_version(connection: sqlite3.Connection) -> int:
    history = read_migration_history(connection)
    return history[-1].version if history else 0


def _iter_statements(script: str) -> Iterator[str]:
    """Yield complete SQLite statements without `executescript` auto-commits."""

    buffer: list[str] = []
    for line in script.splitlines(keepends=True):
        buffer.append(line)
        candidate = "".join(buffer).strip()
        if candidate and sqlite3.complete_statement(candidate):
            yield candidate
            buffer.clear()
    remainder = "".join(buffer).strip()
    if remainder:
        if not sqlite3.complete_statement(remainder):
            raise MigrationError("migration ends with an incomplete SQL statement")
        yield remainder


def _validate_history(history: Iterable[MigrationInfo], migrations: tuple[Migration, ...]) -> None:
    by_version = {migration.version: migration for migration in migrations}
    last_version = 0
    for applied in history:
        if applied.version != last_version + 1:
            raise MigrationIntegrityError("stored migration history is not contiguous")
        known = by_version.get(applied.version)
        if known is None:
            last_version = applied.version
            continue
        if applied.name != known.name or applied.checksum != known.checksum:
            raise MigrationIntegrityError(
                f"applied migration {applied.version} differs from {known.source.name}"
            )
        last_version = applied.version


def apply_migrations(
    connection: sqlite3.Connection,
    directory: Path | str | None = None,
    *,
    backup_path: str | None = None,
) -> MigrationReport:
    """Apply every pending migration in a single explicit transaction per file."""

    migrations = discover_migrations(directory)
    history = read_migration_history(connection)
    _validate_history(history, migrations)
    previous = history[-1].version if history else 0
    supported = migrations[-1].version
    if previous > supported:
        raise NewerSchemaError(previous, supported)

    applied: list[int] = []
    for migration in migrations:
        if migration.version <= previous:
            continue
        try:
            connection.execute("BEGIN IMMEDIATE")
            for statement in _iter_statements(migration.sql):
                connection.execute(statement)
            connection.execute(
                "INSERT INTO schema_version(version, name, checksum, applied_at) "
                "VALUES (?, ?, ?, ?)",
                (migration.version, migration.name, migration.checksum, utc_now()),
            )
            connection.commit()
        except BaseException:
            if connection.in_transaction:
                connection.rollback()
            raise
        applied.append(migration.version)

    return MigrationReport(
        previous_version=previous,
        current_version=supported,
        applied_versions=tuple(applied),
        backup_path=backup_path,
    )
