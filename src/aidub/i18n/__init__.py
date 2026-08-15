"""Runtime localization services for AI Movie Dubbing Studio.

The localization layer intentionally has no Qt dependency.  Desktop, CLI and
worker-facing messages can therefore share the same catalog and fallback
rules, and translation behavior remains testable in headless CI.
"""

from .catalog import (
    DEFAULT_LOCALE,
    CatalogError,
    CatalogNotFoundError,
    CatalogRepository,
    LocaleService,
    TranslationCatalog,
    default_catalog_directory,
    locale_fallback_chain,
    normalize_locale,
    system_locale,
)

__all__ = [
    "DEFAULT_LOCALE",
    "CatalogError",
    "CatalogNotFoundError",
    "CatalogRepository",
    "LocaleService",
    "TranslationCatalog",
    "default_catalog_directory",
    "locale_fallback_chain",
    "normalize_locale",
    "system_locale",
]
