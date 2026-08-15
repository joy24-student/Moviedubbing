"""Application project-catalog exception hierarchy."""

from __future__ import annotations


class CatalogError(RuntimeError):
    """Base class for catalog failures."""


class InvalidCatalogPathError(CatalogError, ValueError):
    """Raised when a catalog or project-package path is unsafe/invalid."""


class CatalogConflictError(CatalogError):
    """Raised when one normalized package path maps to another project ID."""


class CatalogIntegrityError(CatalogError):
    """Raised when SQLite or a stored record fails validation."""


class NewerCatalogSchemaError(CatalogError):
    """Raised before writing a catalog created by a newer application."""

    def __init__(self, found_version: int, supported_version: int) -> None:
        self.found_version = found_version
        self.supported_version = supported_version
        super().__init__(
            f"catalog schema {found_version} is newer than supported schema "
            f"{supported_version}; it was not modified"
        )


class UnrecognizedCatalogError(CatalogError):
    """Raised when a non-empty, unversioned database is used as a catalog."""
