"""Reusable constrained scalar types and small validation helpers."""

from __future__ import annotations

from typing import Annotated, TypeAlias, TypeVar

from pydantic import StringConstraints

NonEmptyStr: TypeAlias = Annotated[
    str,
    StringConstraints(strip_whitespace=True, min_length=1, max_length=512),
]
LongText: TypeAlias = Annotated[
    str,
    StringConstraints(strip_whitespace=True, min_length=1, max_length=100_000),
]
LanguageTag: TypeAlias = Annotated[
    str,
    StringConstraints(
        strip_whitespace=True,
        min_length=2,
        max_length=35,
        pattern=r"^[A-Za-z]{2,8}(?:-[A-Za-z0-9]{1,8})*$",
    ),
]
TerritoryCode: TypeAlias = Annotated[
    str,
    StringConstraints(pattern=r"^(?:[A-Z]{2}|WORLDWIDE)$"),
]
Sha256: TypeAlias = Annotated[
    str,
    StringConstraints(pattern=r"^[0-9a-f]{64}$"),
]
SemanticVersion: TypeAlias = Annotated[
    str,
    StringConstraints(
        pattern=r"^(?:0|[1-9][0-9]*)\.(?:0|[1-9][0-9]*)\.(?:0|[1-9][0-9]*)"
        r"(?:-[0-9A-Za-z.-]+)?(?:\+[0-9A-Za-z.-]+)?$"
    ),
]
MimeType: TypeAlias = Annotated[
    str,
    StringConstraints(pattern=r"^[a-z0-9!#$&^_.+-]+/[a-z0-9!#$&^_.+-]+$", max_length=127),
]

_T = TypeVar("_T")


def require_unique(values: tuple[_T, ...], *, field_name: str) -> tuple[_T, ...]:
    """Reject duplicates while preserving deterministic tuple order."""

    if len(set(values)) != len(values):
        raise ValueError(f"{field_name} must not contain duplicates")
    return values


__all__ = [
    "LanguageTag",
    "LongText",
    "MimeType",
    "NonEmptyStr",
    "SemanticVersion",
    "Sha256",
    "TerritoryCode",
    "require_unique",
]
