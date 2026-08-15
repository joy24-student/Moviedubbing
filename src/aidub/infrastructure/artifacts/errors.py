"""Artifact-store exception hierarchy."""

from __future__ import annotations


class ArtifactStoreError(RuntimeError):
    """Base class for immutable artifact storage failures."""


class UnsafeArtifactPathError(ArtifactStoreError):
    """Raised when a path could escape or redirect the managed store."""


class InvalidArtifactHashError(ArtifactStoreError, ValueError):
    """Raised when a caller supplies something other than a SHA-256 hex digest."""


class ArtifactHashMismatchError(ArtifactStoreError):
    """Raised when staged bytes do not match their declared digest."""


class ArtifactSizeMismatchError(ArtifactStoreError):
    """Raised when staged bytes do not match their declared length."""


class CorruptArtifactError(ArtifactStoreError):
    """Raised when an existing content-addressed object fails validation."""


class UnknownStageError(ArtifactStoreError):
    """Raised when a staged artifact token/path is not owned by this store."""
