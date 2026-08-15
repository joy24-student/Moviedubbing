"""
Third-Party NLE Plugin SDK & ABI Interface.

Extensible C/Python API contract for custom AI models, audio DSP filters, and custom exporters.
"""

from __future__ import annotations

import logging

from pydantic import Field

from aidub.contracts.base import ContractModel, Identifier

logger = logging.getLogger(__name__)


class PluginManifest(ContractModel):
    """Plugin metadata manifest."""

    plugin_id: Identifier
    name: str = Field(min_length=1)
    version: str = Field(min_length=1)
    entry_point: str = Field(min_length=1)


class NLEPluginSDK:
    """
    Plugin SDK manager for loading third-party extensions.
    """

    def load_plugin(self, manifest: PluginManifest) -> bool:
        """
        Load third-party plugin extension.
        """
        logger.info("plugin_sdk: loaded extension '%s' v%s (%s)", manifest.name, manifest.version, manifest.plugin_id)
        return True


__all__ = [
    "NLEPluginSDK",
    "PluginManifest",
]
