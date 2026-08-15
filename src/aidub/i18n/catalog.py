"""JSON-backed, deterministic translation catalog support.

Catalog files are deliberately simple and reviewable by translators.  A
catalog contains a ``meta`` object and a flat ``strings`` mapping.  Flat keys
make missing-string reports and translation-memory exports straightforward.
"""

from __future__ import annotations

import json
import locale as system_locale_module
import os
import re
import sys
from collections.abc import Callable, Iterable, Mapping
from dataclasses import dataclass
from pathlib import Path
from threading import RLock
from types import MappingProxyType
from typing import Any

DEFAULT_LOCALE = "en"
CATALOG_ENVIRONMENT_VARIABLE = "AIDUB_I18N_DIR"
_LOCALE_PARTS = re.compile(r"^[A-Za-z]{2,8}(?:[-_][A-Za-z0-9]{2,8})*$")


class CatalogError(RuntimeError):
    """A translation catalog exists but is malformed."""


class CatalogNotFoundError(CatalogError):
    """No translation catalog can satisfy a requested locale."""


@dataclass(frozen=True, slots=True)
class TranslationCatalog:
    """An immutable set of translated strings for one locale."""

    locale: str
    strings: Mapping[str, str]
    display_name: str
    native_name: str
    direction: str = "ltr"
    version: int = 1

    def get(self, key: str) -> str | None:
        return self.strings.get(key)


def normalize_locale(value: str | None) -> str:
    """Return a small BCP-47-style locale identifier.

    OS locale values often include an encoding (``bn_BD.UTF-8``) or modifier.
    Those suffixes do not participate in catalog selection and are removed.
    Invalid or empty values safely resolve to English.
    """

    if value is None:
        return DEFAULT_LOCALE
    candidate = str(value).strip()
    if not candidate or candidate.upper() in {"C", "POSIX"}:
        return DEFAULT_LOCALE
    candidate = candidate.split(".", 1)[0].split("@", 1)[0]
    if not _LOCALE_PARTS.fullmatch(candidate):
        return DEFAULT_LOCALE

    parts = candidate.replace("_", "-").split("-")
    normalized = [parts[0].lower()]
    for part in parts[1:]:
        if len(part) == 4 and part.isalpha():
            normalized.append(part.title())
        elif len(part) in {2, 3}:
            normalized.append(part.upper())
        else:
            normalized.append(part.lower())
    return "-".join(normalized)


def _matching_variant(language: str, available: tuple[str, ...]) -> str | None:
    prefix = f"{language}-"
    return next((item for item in available if item.startswith(prefix)), None)


def locale_fallback_chain(
    requested: str | None,
    available: Iterable[str],
    fallback: str = DEFAULT_LOCALE,
) -> tuple[str, ...]:
    """Build the locale lookup order, including language and global fallback.

    A language-only request such as ``bn`` selects the installed regional
    catalog ``bn-BD``.  Conversely, ``en-GB`` falls back to ``en``.
    """

    installed = tuple(dict.fromkeys(normalize_locale(item) for item in available))
    if not installed:
        return ()

    result: list[str] = []

    def add(locale_name: str | None) -> None:
        normalized = normalize_locale(locale_name)
        language = normalized.split("-", 1)[0]
        candidates = (normalized, language, _matching_variant(language, installed))
        for candidate in candidates:
            if candidate and candidate in installed and candidate not in result:
                result.append(candidate)

    add(requested)
    add(fallback)
    add(DEFAULT_LOCALE)
    return tuple(result)


def system_locale() -> str:
    """Return the operating-system locale without raising during startup."""

    try:
        detected = system_locale_module.getlocale()[0]
    except (ValueError, TypeError):
        detected = None
    return normalize_locale(detected)


def default_catalog_directory() -> Path:
    """Locate catalogs in development, packaged and operator-overridden runs."""

    configured = os.environ.get(CATALOG_ENVIRONMENT_VARIABLE)
    if configured:
        return Path(configured).expanduser().resolve()

    candidates: list[Path] = []
    bundle_root = getattr(sys, "_MEIPASS", None)
    if bundle_root:
        candidates.append(Path(bundle_root) / "resources" / "i18n")
    candidates.append(Path(__file__).resolve().parent / "catalogs")
    candidates.append(Path(sys.executable).resolve().parent / "resources" / "i18n")
    candidates.append(Path(__file__).resolve().parents[3] / "resources" / "i18n")
    return next((path for path in candidates if path.is_dir()), candidates[-1])


class CatalogRepository:
    """Load and cache validated catalogs from a directory."""

    def __init__(self, directory: str | Path | None = None) -> None:
        self.directory = Path(directory) if directory is not None else default_catalog_directory()
        self._cache: dict[str, TranslationCatalog] = {}
        self._lock = RLock()

    def available_locales(self) -> tuple[str, ...]:
        if not self.directory.is_dir():
            return ()
        locales = (
            normalize_locale(path.stem)
            for path in self.directory.glob("*.json")
            if _LOCALE_PARTS.fullmatch(path.stem)
        )
        return tuple(
            sorted(dict.fromkeys(locales), key=lambda item: (item != DEFAULT_LOCALE, item))
        )

    def load(self, locale_name: str) -> TranslationCatalog:
        normalized = normalize_locale(locale_name)
        with self._lock:
            cached = self._cache.get(normalized)
            if cached is not None:
                return cached

            path = self.directory / f"{normalized}.json"
            if not path.is_file():
                raise CatalogNotFoundError(
                    f"Translation catalog '{normalized}' was not found in {self.directory}."
                )
            try:
                payload = json.loads(path.read_text(encoding="utf-8"))
            except (OSError, UnicodeError, json.JSONDecodeError) as exc:
                raise CatalogError(f"Cannot read translation catalog {path}: {exc}") from exc

            catalog = self._validate_payload(payload, normalized, path)
            self._cache[normalized] = catalog
            return catalog

    def clear_cache(self) -> None:
        with self._lock:
            self._cache.clear()

    @staticmethod
    def _validate_payload(payload: Any, expected_locale: str, source: Path) -> TranslationCatalog:
        if not isinstance(payload, dict):
            raise CatalogError(f"Catalog {source} must contain a JSON object.")
        metadata = payload.get("meta", {})
        strings = payload.get("strings")
        if not isinstance(metadata, dict) or not isinstance(strings, dict):
            raise CatalogError(f"Catalog {source} requires object-valued 'meta' and 'strings'.")

        declared_locale = normalize_locale(metadata.get("locale", expected_locale))
        if declared_locale != expected_locale:
            raise CatalogError(
                f"Catalog {source} declares locale '{declared_locale}', "
                f"expected '{expected_locale}'."
            )
        invalid = [
            key
            for key, value in strings.items()
            if not isinstance(key, str) or not isinstance(value, str)
        ]
        if invalid:
            raise CatalogError(f"Catalog {source} has non-text translation values: {invalid[:3]}")
        direction = metadata.get("direction", "ltr")
        if direction not in {"ltr", "rtl"}:
            raise CatalogError(f"Catalog {source} has unsupported text direction '{direction}'.")
        version = metadata.get("version", 1)
        if not isinstance(version, int) or isinstance(version, bool) or version < 1:
            raise CatalogError(f"Catalog {source} has an invalid positive integer version.")

        return TranslationCatalog(
            locale=declared_locale,
            strings=MappingProxyType(dict(strings)),
            display_name=str(metadata.get("display_name", declared_locale)),
            native_name=str(
                metadata.get("native_name", metadata.get("display_name", declared_locale))
            ),
            direction=direction,
            version=version,
        )


class _SafeFormatValues(dict[str, object]):
    def __missing__(self, key: str) -> str:
        return "{" + key + "}"


LocaleListener = Callable[[str], None]


class LocaleService:
    """Resolve translated UI text and notify listeners when locale changes."""

    def __init__(
        self,
        locale: str | None = None,
        *,
        repository: CatalogRepository | None = None,
        fallback_locale: str = DEFAULT_LOCALE,
    ) -> None:
        self._repository = repository or CatalogRepository()
        self._fallback_locale = normalize_locale(fallback_locale)
        self._listeners: list[LocaleListener] = []
        self._lock = RLock()
        available = self._repository.available_locales()
        if not available:
            raise CatalogNotFoundError(
                f"No JSON translation catalogs were found in {self._repository.directory}."
            )
        self._requested_locale = normalize_locale(locale or system_locale())
        chain = locale_fallback_chain(self._requested_locale, available, self._fallback_locale)
        if not chain:
            raise CatalogNotFoundError(
                f"Locale '{self._requested_locale}' cannot be resolved from {available}."
            )
        self._locale = chain[0]

    @property
    def locale(self) -> str:
        return self._locale

    @property
    def requested_locale(self) -> str:
        return self._requested_locale

    @property
    def direction(self) -> str:
        return self._repository.load(self._locale).direction

    def available_locales(self) -> tuple[str, ...]:
        return self._repository.available_locales()

    def catalogs(self) -> tuple[TranslationCatalog, ...]:
        return tuple(self._repository.load(item) for item in self.available_locales())

    def set_locale(self, locale_name: str) -> str:
        requested = normalize_locale(locale_name)
        available = self.available_locales()
        chain = locale_fallback_chain(requested, available, self._fallback_locale)
        if not chain:
            raise CatalogNotFoundError(f"Locale '{requested}' cannot be resolved from {available}.")
        resolved = chain[0]
        with self._lock:
            self._requested_locale = requested
            if resolved == self._locale:
                return resolved
            self._locale = resolved
            listeners = tuple(self._listeners)
        for listener in listeners:
            listener(resolved)
        return resolved

    def subscribe(self, listener: LocaleListener) -> Callable[[], None]:
        with self._lock:
            if listener not in self._listeners:
                self._listeners.append(listener)

        def unsubscribe() -> None:
            with self._lock:
                if listener in self._listeners:
                    self._listeners.remove(listener)

        return unsubscribe

    def translate(self, key: str, default: str | None = None, /, **values: object) -> str:
        if not isinstance(key, str) or not key:
            raise ValueError("Translation key must be a non-empty string.")
        available = self.available_locales()
        chain = locale_fallback_chain(self._locale, available, self._fallback_locale)
        template: str | None = None
        for locale_name in chain:
            template = self._repository.load(locale_name).get(key)
            if template is not None:
                break
        if template is None:
            template = default if default is not None else key
        if not values:
            return template
        try:
            return template.format_map(_SafeFormatValues(values))
        except (ValueError, TypeError):
            # A translator typo must never prevent the shell from opening.
            return template

    __call__ = translate
