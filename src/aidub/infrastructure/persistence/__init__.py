"""Project persistence public API."""

from .database import ProjectDatabase
from .errors import (
    DatabaseNotInitializedError,
    IntegrityCheckError,
    InvalidStateTransitionError,
    MigrationError,
    MigrationIntegrityError,
    NewerSchemaError,
    PersistenceError,
)
from .migrations import current_schema_version, discover_migrations, latest_supported_version
from .models import (
    ArtifactRecord,
    ArtifactStatus,
    AuditEventRecord,
    IntegrityReport,
    JobRecord,
    JobState,
    MigrationInfo,
    MigrationReport,
    ProjectRecord,
    ReproducibilityLevel,
)

__all__ = [
    "ArtifactRecord",
    "ArtifactStatus",
    "AuditEventRecord",
    "DatabaseNotInitializedError",
    "IntegrityCheckError",
    "IntegrityReport",
    "InvalidStateTransitionError",
    "JobRecord",
    "JobState",
    "MigrationError",
    "MigrationInfo",
    "MigrationIntegrityError",
    "MigrationReport",
    "NewerSchemaError",
    "PersistenceError",
    "ProjectDatabase",
    "ProjectRecord",
    "ReproducibilityLevel",
    "current_schema_version",
    "discover_migrations",
    "latest_supported_version",
]
