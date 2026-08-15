"""Shared behavior for pure domain value objects and entities."""

from __future__ import annotations

from collections.abc import Mapping
from datetime import UTC, datetime
from typing import Annotated, Any, ClassVar, TypeAlias, TypeVar

from pydantic import AfterValidator, BaseModel, ConfigDict, model_validator

_Key = TypeVar("_Key")
_Value = TypeVar("_Value")


class FrozenDict(dict[_Key, _Value]):
    """Serialization-friendly immutable dictionary used inside frozen domain models."""

    @staticmethod
    def _immutable(*_args: object, **_kwargs: object) -> None:
        raise TypeError("domain mappings are immutable")

    __delitem__ = _immutable
    __ior__ = _immutable  # type: ignore[assignment]
    __setitem__ = _immutable
    clear = _immutable
    pop = _immutable  # type: ignore[assignment]
    popitem = _immutable  # type: ignore[assignment]
    setdefault = _immutable  # type: ignore[assignment]
    update = _immutable


def _deep_freeze(value: Any) -> Any:
    if isinstance(value, DomainModel):
        return value
    if isinstance(value, Mapping):
        return FrozenDict((key, _deep_freeze(item)) for key, item in value.items())
    if isinstance(value, list | tuple):
        return tuple(_deep_freeze(item) for item in value)
    if isinstance(value, set | frozenset):
        return frozenset(_deep_freeze(item) for item in value)
    return value


def utc_now() -> datetime:
    """Return a timezone-aware UTC timestamp.

    Time is injected into state-changing helpers where deterministic tests or replay are needed;
    this function is only the boundary default.
    """

    return datetime.now(UTC)


def normalize_utc(value: datetime) -> datetime:
    """Validate an aware timestamp and normalize it to UTC."""

    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError("timestamp must be timezone-aware")
    return value.astimezone(UTC)


UtcDatetime: TypeAlias = Annotated[datetime, AfterValidator(normalize_utc)]


class DomainModel(BaseModel):
    """Strict and immutable base for persisted domain contracts."""

    model_config: ClassVar[ConfigDict] = ConfigDict(
        extra="forbid",
        frozen=True,
        strict=True,
        str_strip_whitespace=True,
        validate_default=True,
    )

    @model_validator(mode="after")
    def _freeze_nested_collections(self) -> DomainModel:
        for field_name in type(self).model_fields:
            value = getattr(self, field_name)
            frozen = _deep_freeze(value)
            if frozen is not value:
                object.__setattr__(self, field_name, frozen)
        return self


class DomainError(Exception):
    """Base class for a rejected domain operation."""


class RightsViolation(DomainError):
    """Raised when a requested use is outside an authorization grant."""


class InvalidStateTransition(DomainError):
    """Raised when an entity state machine rejects a transition."""
