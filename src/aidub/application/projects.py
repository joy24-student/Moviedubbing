"""Crash-safe project-package creation, validation, and startup recovery."""

from __future__ import annotations

import os
import stat
import tempfile
from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path
from typing import Final, Self
from uuid import uuid4

from pydantic import TypeAdapter, ValidationError

from aidub.domain.identifiers import new_id
from aidub.domain.project import Project, ProjectSettings, ProjectState
from aidub.domain.rights import SourceAuthorization
from aidub.domain.types import LanguageTag
from aidub.infrastructure.artifacts import ArtifactStore, ReconciliationReport
from aidub.infrastructure.catalog import CatalogError, ProjectCatalog
from aidub.infrastructure.locking import ProjectLock
from aidub.infrastructure.persistence import (
    AuditEventRecord,
    MigrationReport,
    ProjectDatabase,
    ProjectRecord,
)

PROJECT_SUFFIX: Final = ".aidub"
MANIFEST_FILENAME: Final = "manifest.json"
DATABASE_FILENAME: Final = "project.db"
SUPPORTED_MANIFEST_VERSION: Final = 1
MAX_MANIFEST_BYTES: Final = 8 * 1024 * 1024

_PACKAGE_DIRECTORIES: Final = (
    "source-links",
    "proxy",
    "thumbnails",
    "waveforms",
    "artifacts",
    "localizations",
    "renders",
    "recovery",
    "logs",
    "cache",
    "stems",
    "transcripts",
)
_LANGUAGE_TAG = TypeAdapter(LanguageTag)


class ProjectPackageError(RuntimeError):
    """Base class for project-package lifecycle failures."""


class ProjectAlreadyExistsError(ProjectPackageError):
    """Raised when creation would replace an existing filesystem object."""


class InvalidProjectPackageError(ProjectPackageError):
    """Raised when a package is incomplete, unsafe, or has an invalid manifest."""


class ProjectManifestMismatchError(InvalidProjectPackageError):
    """Raised when the manifest and authoritative database disagree."""


@dataclass(frozen=True, slots=True)
class ProjectPackagePaths:
    """Well-known paths inside one active ``.aidub`` directory."""

    root: Path
    manifest: Path
    database: Path
    source_links: Path
    proxy: Path
    thumbnails: Path
    waveforms: Path
    artifacts: Path
    localizations: Path
    renders: Path
    recovery: Path
    logs: Path
    cache: Path
    stems: Path
    transcripts: Path

    @classmethod
    def at(cls, root: Path | str) -> ProjectPackagePaths:
        package_root = Path(root).expanduser().resolve(strict=False)
        return cls(
            root=package_root,
            manifest=package_root / MANIFEST_FILENAME,
            database=package_root / DATABASE_FILENAME,
            source_links=package_root / "source-links",
            proxy=package_root / "proxy",
            thumbnails=package_root / "thumbnails",
            waveforms=package_root / "waveforms",
            artifacts=package_root / "artifacts",
            localizations=package_root / "localizations",
            renders=package_root / "renders",
            recovery=package_root / "recovery",
            logs=package_root / "logs",
            cache=package_root / "cache",
            stems=package_root / "stems",
            transcripts=package_root / "transcripts",
        )


@dataclass(frozen=True, slots=True)
class OpenedProject:
    """Validated runtime handles returned by create/open use cases."""

    project: Project
    paths: ProjectPackagePaths
    database: ProjectDatabase
    artifact_store: ArtifactStore
    migration: MigrationReport
    recovered_job_ids: tuple[str, ...]
    artifact_reconciliation: ReconciliationReport
    project_lock: ProjectLock | None = None
    catalog_registered: bool = False
    warnings: tuple[str, ...] = ()

    @property
    def holds_exclusive_lock(self) -> bool:
        return self.project_lock is not None and self.project_lock.held

    def close(self) -> None:
        """Release a long-lived editing lock; repeated calls are safe."""

        if self.project_lock is not None:
            self.project_lock.release()

    def __enter__(self) -> Self:
        return self

    def __exit__(self, _exc_type: object, _exc: object, _traceback: object) -> None:
        self.close()


def _is_link_or_reparse(path: Path) -> bool:
    try:
        info = path.lstat()
    except FileNotFoundError:
        return False
    if stat.S_ISLNK(info.st_mode):
        return True
    reparse_flag = getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0)
    return bool(getattr(info, "st_file_attributes", 0) & reparse_flag)


def _package_destination(requested: Path | str) -> Path:
    destination = Path(requested).expanduser()
    if destination.suffix.casefold() != PROJECT_SUFFIX:
        destination = destination.with_name(f"{destination.name}{PROJECT_SUFFIX}")
    return destination.resolve(strict=False)


def _project_state_for_database(state: ProjectState) -> str:
    if state is ProjectState.ACTIVE:
        return "ACTIVE"
    if state is ProjectState.ARCHIVED:
        return "ARCHIVED"
    if state is ProjectState.READ_ONLY:
        return "READ_ONLY"
    return "RECOVERY_REQUIRED"


def _write_manifest(path: Path, project: Project) -> None:
    temporary = path.with_name(f".{path.name}.{uuid4().hex}.tmp")
    payload = project.model_dump_json(indent=2)
    try:
        with temporary.open("x", encoding="utf-8", newline="\n") as stream:
            stream.write(payload)
            stream.write("\n")
            stream.flush()
            os.fsync(stream.fileno())
        temporary.replace(path)
    finally:
        temporary.unlink(missing_ok=True)


def _load_manifest(path: Path) -> Project:
    if _is_link_or_reparse(path) or not path.is_file():
        raise InvalidProjectPackageError(f"project manifest is missing or unsafe: {path}")
    size = path.stat().st_size
    if size <= 0 or size > MAX_MANIFEST_BYTES:
        raise InvalidProjectPackageError(
            f"project manifest size must be between 1 and {MAX_MANIFEST_BYTES} bytes"
        )
    try:
        raw = path.read_text(encoding="utf-8")
        project = Project.model_validate_json(raw)
    except (OSError, UnicodeError, ValidationError) as exc:
        raise InvalidProjectPackageError(f"project manifest is invalid: {path}") from exc
    if project.schema_version > SUPPORTED_MANIFEST_VERSION:
        raise InvalidProjectPackageError(
            "project manifest uses a newer unsupported schema "
            f"({project.schema_version} > {SUPPORTED_MANIFEST_VERSION})"
        )
    return project


def _validate_locales(locales: Iterable[str]) -> tuple[str, ...]:
    validated = tuple(_LANGUAGE_TAG.validate_python(locale, strict=True) for locale in locales)
    if len({item.casefold() for item in validated}) != len(validated):
        raise ValueError("localization language tags must be unique")
    return validated


def _assert_manifest_matches(project: Project, stored: ProjectRecord | None) -> None:
    if stored is None:
        raise ProjectManifestMismatchError(
            f"manifest project {project.project_id} is absent from the database"
        )
    expected_settings = project.settings.model_dump(mode="json")
    differences = {
        key
        for key, matches in {
            "name": stored.name == project.name,
            "source_language": stored.source_language == project.settings.source_language,
            "settings": dict(stored.settings) == expected_settings,
            "state": stored.state == _project_state_for_database(project.state),
            "revision": stored.revision == project.revision,
        }.items()
        if not matches
    }
    if differences:
        fields = ", ".join(sorted(differences))
        raise ProjectManifestMismatchError(f"project manifest and database disagree on: {fields}")


def _validate_package_directories(paths: ProjectPackagePaths) -> None:
    for directory_name in _PACKAGE_DIRECTORIES:
        directory = paths.root / directory_name
        if _is_link_or_reparse(directory) or not directory.is_dir():
            raise InvalidProjectPackageError(
                f"required project directory is missing or unsafe: {directory}"
            )


class ProjectPackageService:
    """Create and open local-first projects without exposing partial packages."""

    def __init__(self, *, catalog: ProjectCatalog | None = None) -> None:
        self.catalog = catalog

    def create(
        self,
        destination: Path | str,
        *,
        name: str,
        settings: ProjectSettings,
        source_authorization: SourceAuthorization,
        localization_locales: Iterable[str] = (),
        actor_id: str | None = None,
        hold_lock: bool = False,
    ) -> OpenedProject:
        """Atomically publish a fully initialized active project directory."""

        final_root = _package_destination(destination)
        if final_root.exists() or final_root.is_symlink():
            raise ProjectAlreadyExistsError(f"project destination already exists: {final_root}")
        final_root.parent.mkdir(parents=True, exist_ok=True)
        if not final_root.parent.is_dir() or _is_link_or_reparse(final_root.parent):
            raise InvalidProjectPackageError(
                f"project parent is not a safe directory: {final_root.parent}"
            )

        locales = _validate_locales(localization_locales)
        project = Project(
            project_id=new_id("prj"),
            name=name,
            settings=settings,
            source_authorization=source_authorization,
        )

        with tempfile.TemporaryDirectory(
            prefix=f".{final_root.stem}.creating-", dir=final_root.parent
        ) as temporary_directory:
            staging_root = Path(temporary_directory)
            staging = ProjectPackagePaths.at(staging_root)
            for directory_name in _PACKAGE_DIRECTORIES:
                (staging.root / directory_name).mkdir()
            for locale in locales:
                (staging.localizations / locale).mkdir()
            _write_manifest(staging.manifest, project)

            database = ProjectDatabase(staging.database)
            database.initialize(backup_before_migration=False)
            database.create_project(
                ProjectRecord(
                    id=project.project_id,
                    name=project.name,
                    source_language=project.settings.source_language,
                    settings=project.settings.model_dump(mode="json"),
                    state=_project_state_for_database(project.state),
                    created_at=project.created_at.isoformat(),
                    updated_at=project.updated_at.isoformat(),
                    revision=project.revision,
                )
            )
            database.append_audit_event(
                AuditEventRecord(
                    id=f"evt_{uuid4().hex}",
                    project_id=project.project_id,
                    action="PROJECT_CREATED",
                    actor_type="USER" if actor_id else "SYSTEM",
                    actor_id=actor_id,
                    target_type="PROJECT",
                    target_id=project.project_id,
                    details={
                        "manifest_schema_version": project.schema_version,
                        "localization_locales": list(locales),
                    },
                )
            )
            ArtifactStore(staging.artifacts)
            database.checkpoint_wal(truncate=True)

            if final_root.exists() or final_root.is_symlink():
                raise ProjectAlreadyExistsError(
                    f"project destination appeared during creation: {final_root}"
                )
            staging.root.replace(final_root)

        return self.open(
            final_root,
            recover_interrupted=False,
            hold_lock=hold_lock,
        )

    def open(
        self,
        package: Path | str,
        *,
        recover_interrupted: bool = True,
        reconcile_artifacts: bool = True,
        hold_lock: bool = False,
    ) -> OpenedProject:
        """Validate, migrate, reconcile, and return one active project package."""

        requested = Path(package).expanduser()
        if _is_link_or_reparse(requested):
            raise InvalidProjectPackageError(f"project package cannot be a link: {requested}")
        root = requested.resolve(strict=False)
        if root.suffix.casefold() != PROJECT_SUFFIX or not root.is_dir():
            raise InvalidProjectPackageError(f"not an .aidub project directory: {root}")
        paths = ProjectPackagePaths.at(root)
        _validate_package_directories(paths)
        if _is_link_or_reparse(paths.database) or not paths.database.is_file():
            raise InvalidProjectPackageError(
                f"project database is missing or unsafe: {paths.database}"
            )

        lock = ProjectLock(root)
        lock.acquire()
        try:
            project = _load_manifest(paths.manifest)
            database = ProjectDatabase(paths.database)
            migration = database.initialize()
            stored = database.get_project(project.project_id)
            _assert_manifest_matches(project, stored)

            recovered = database.recover_interrupted_jobs() if recover_interrupted else ()
            if recovered:
                database.append_audit_event(
                    AuditEventRecord(
                        id=f"evt_{uuid4().hex}",
                        project_id=project.project_id,
                        action="INTERRUPTED_JOBS_RECOVERED",
                        actor_type="SYSTEM",
                        target_type="PROJECT",
                        target_id=project.project_id,
                        details={"job_ids": list(recovered)},
                    )
                )

            artifact_store = ArtifactStore(paths.artifacts)
            inventory = database.artifact_inventory(project.project_id)
            reconciliation = artifact_store.reconcile(
                inventory if reconcile_artifacts else None,
                remove_abandoned_stages=reconcile_artifacts,
                full_hash=reconcile_artifacts,
            )
            catalog_registered, warnings = self._register_catalog(project, paths)
            opened = OpenedProject(
                project=project,
                paths=paths,
                database=database,
                artifact_store=artifact_store,
                migration=migration,
                recovered_job_ids=recovered,
                artifact_reconciliation=reconciliation,
                project_lock=lock if hold_lock else None,
                catalog_registered=catalog_registered,
                warnings=warnings,
            )
        except BaseException:
            lock.release()
            raise
        else:
            if not hold_lock:
                lock.release()
            return opened

    def open_session(
        self,
        package: Path | str,
        *,
        recover_interrupted: bool = True,
        reconcile_artifacts: bool = True,
    ) -> OpenedProject:
        """Open a project and retain exclusive ownership until ``close``."""

        return self.open(
            package,
            recover_interrupted=recover_interrupted,
            reconcile_artifacts=reconcile_artifacts,
            hold_lock=True,
        )

    def _register_catalog(
        self,
        project: Project,
        paths: ProjectPackagePaths,
    ) -> tuple[bool, tuple[str, ...]]:
        if self.catalog is None:
            return False, ()
        try:
            self.catalog.initialize()
            self.catalog.upsert_project(
                project_id=project.project_id,
                name=project.name,
                path=paths.root,
            )
        except (CatalogError, OSError) as exc:
            warning = f"project catalog was not updated: {type(exc).__name__}: {exc}"
            return False, (warning[:1_000],)
        return True, ()


__all__ = [
    "DATABASE_FILENAME",
    "MANIFEST_FILENAME",
    "PROJECT_SUFFIX",
    "SUPPORTED_MANIFEST_VERSION",
    "InvalidProjectPackageError",
    "OpenedProject",
    "ProjectAlreadyExistsError",
    "ProjectManifestMismatchError",
    "ProjectPackageError",
    "ProjectPackagePaths",
    "ProjectPackageService",
]
