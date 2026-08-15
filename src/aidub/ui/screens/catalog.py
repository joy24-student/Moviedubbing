"""
Complete catalog of 26 workspace screens specified in Master Spec Section 27.

Screens:
  1. Home / Dashboard           10. Performance Studio      19. Model Manager
  2. New Project Wizard        11. Timeline Editor         20. GPU & Performance
  3. Media Inspector           12. Lip-Sync Studio         21. Storage & Cache
  4. Analysis Center           13. Audio Mixer             22. Privacy & Rights
  5. Scene Browser             14. Subtitle Studio         23. Diagnostics
  6. Character Studio          15. Quality Control         24. Settings
  7. Voice Studio              16. Render Queue            25. Help & Docs
  8. Translation Studio        17. Export Center           26. License Manager
  9. Pronunciation Studio      18. Provider Manager
"""

from __future__ import annotations

from enum import StrEnum

from pydantic import Field

from aidub.contracts.base import ContractModel


class ScreenCategory(StrEnum):
    WORKSPACE = "workspace"
    STUDIO = "studio"
    EDITOR = "editor"
    OPERATIONS = "operations"
    SETTINGS = "settings"


class ScreenId(StrEnum):
    HOME_DASHBOARD = "home_dashboard"
    NEW_PROJECT_WIZARD = "new_project_wizard"
    MEDIA_INSPECTOR = "media_inspector"
    ANALYSIS_CENTER = "analysis_center"
    SCENE_BROWSER = "scene_browser"

    CHARACTER_STUDIO = "character_studio"
    VOICE_STUDIO = "voice_studio"
    TRANSLATION_STUDIO = "translation_studio"
    PRONUNCIATION_STUDIO = "pronunciation_studio"
    PERFORMANCE_STUDIO = "performance_studio"

    TIMELINE_EDITOR = "timeline_editor"
    LIPSYNC_STUDIO = "lipsync_studio"
    AUDIO_MIXER = "audio_mixer"
    SUBTITLE_STUDIO = "subtitle_studio"
    QUALITY_CONTROL = "quality_control"

    RENDER_QUEUE = "render_queue"
    EXPORT_CENTER = "export_center"
    PROVIDER_MANAGER = "provider_manager"
    MODEL_MANAGER = "model_manager"
    GPU_PERFORMANCE = "gpu_performance"

    STORAGE_CACHE = "storage_cache"
    PRIVACY_RIGHTS = "privacy_rights"
    DIAGNOSTICS = "diagnostics"
    SETTINGS = "settings"
    HELP_DOCS = "help_docs"
    LICENSE_MANAGER = "license_manager"


class ScreenDescriptor(ContractModel):
    """Metadata descriptor for a single desktop workspace screen."""

    screen_id: ScreenId
    title: str = Field(min_length=1, max_length=128)
    category: ScreenCategory
    icon_name: str = Field(default="folder", max_length=64)
    keyboard_shortcut: str = Field(default="", max_length=32)
    enabled: bool = True


SCREEN_CATALOG: list[ScreenDescriptor] = [
    # Workspaces
    ScreenDescriptor(screen_id=ScreenId.HOME_DASHBOARD, title="Home / Dashboard", category=ScreenCategory.WORKSPACE, icon_name="dashboard", keyboard_shortcut="Ctrl+1"),
    ScreenDescriptor(screen_id=ScreenId.NEW_PROJECT_WIZARD, title="New Project Wizard", category=ScreenCategory.WORKSPACE, icon_name="folder-plus"),
    ScreenDescriptor(screen_id=ScreenId.MEDIA_INSPECTOR, title="Media Inspector", category=ScreenCategory.WORKSPACE, icon_name="file-video"),
    ScreenDescriptor(screen_id=ScreenId.ANALYSIS_CENTER, title="Analysis Center", category=ScreenCategory.WORKSPACE, icon_name="cpu"),
    ScreenDescriptor(screen_id=ScreenId.SCENE_BROWSER, title="Scene Browser", category=ScreenCategory.WORKSPACE, icon_name="film"),

    # Studios
    ScreenDescriptor(screen_id=ScreenId.CHARACTER_STUDIO, title="Character Studio", category=ScreenCategory.STUDIO, icon_name="user", keyboard_shortcut="Ctrl+2"),
    ScreenDescriptor(screen_id=ScreenId.VOICE_STUDIO, title="Voice Studio", category=ScreenCategory.STUDIO, icon_name="mic", keyboard_shortcut="Ctrl+3"),
    ScreenDescriptor(screen_id=ScreenId.TRANSLATION_STUDIO, title="Translation Studio", category=ScreenCategory.STUDIO, icon_name="globe", keyboard_shortcut="Ctrl+4"),
    ScreenDescriptor(screen_id=ScreenId.PRONUNCIATION_STUDIO, title="Pronunciation Studio", category=ScreenCategory.STUDIO, icon_name="volume-2"),
    ScreenDescriptor(screen_id=ScreenId.PERFORMANCE_STUDIO, title="Performance Studio", category=ScreenCategory.STUDIO, icon_name="activity"),

    # Editors
    ScreenDescriptor(screen_id=ScreenId.TIMELINE_EDITOR, title="Timeline Editor", category=ScreenCategory.EDITOR, icon_name="sliders", keyboard_shortcut="Ctrl+5"),
    ScreenDescriptor(screen_id=ScreenId.LIPSYNC_STUDIO, title="Lip-Sync Studio", category=ScreenCategory.EDITOR, icon_name="smile", keyboard_shortcut="Ctrl+6"),
    ScreenDescriptor(screen_id=ScreenId.AUDIO_MIXER, title="Audio Mixer", category=ScreenCategory.EDITOR, icon_name="music", keyboard_shortcut="Ctrl+7"),
    ScreenDescriptor(screen_id=ScreenId.SUBTITLE_STUDIO, title="Subtitle Studio", category=ScreenCategory.EDITOR, icon_name="type", keyboard_shortcut="Ctrl+8"),
    ScreenDescriptor(screen_id=ScreenId.QUALITY_CONTROL, title="Quality Control", category=ScreenCategory.EDITOR, icon_name="check-square", keyboard_shortcut="Ctrl+9"),

    # Operations
    ScreenDescriptor(screen_id=ScreenId.RENDER_QUEUE, title="Render Queue", category=ScreenCategory.OPERATIONS, icon_name="play-circle"),
    ScreenDescriptor(screen_id=ScreenId.EXPORT_CENTER, title="Export Center", category=ScreenCategory.OPERATIONS, icon_name="download"),
    ScreenDescriptor(screen_id=ScreenId.PROVIDER_MANAGER, title="Provider Manager", category=ScreenCategory.OPERATIONS, icon_name="server"),
    ScreenDescriptor(screen_id=ScreenId.MODEL_MANAGER, title="Model Manager", category=ScreenCategory.OPERATIONS, icon_name="layers"),
    ScreenDescriptor(screen_id=ScreenId.GPU_PERFORMANCE, title="GPU & Performance", category=ScreenCategory.OPERATIONS, icon_name="zap"),

    # Settings & Admin
    ScreenDescriptor(screen_id=ScreenId.STORAGE_CACHE, title="Storage & Cache", category=ScreenCategory.SETTINGS, icon_name="hard-drive"),
    ScreenDescriptor(screen_id=ScreenId.PRIVACY_RIGHTS, title="Privacy & Rights", category=ScreenCategory.SETTINGS, icon_name="shield"),
    ScreenDescriptor(screen_id=ScreenId.DIAGNOSTICS, title="Diagnostics", category=ScreenCategory.SETTINGS, icon_name="terminal"),
    ScreenDescriptor(screen_id=ScreenId.SETTINGS, title="Settings", category=ScreenCategory.SETTINGS, icon_name="settings", keyboard_shortcut="Ctrl+,"),
    ScreenDescriptor(screen_id=ScreenId.HELP_DOCS, title="Help & Docs", category=ScreenCategory.SETTINGS, icon_name="help-circle"),
    ScreenDescriptor(screen_id=ScreenId.LICENSE_MANAGER, title="License Manager", category=ScreenCategory.SETTINGS, icon_name="key"),
]


class ScreenCatalogRegistry:
    """Registry providing navigation and lookup for all 26 workspace screens."""

    def __init__(self) -> None:
        self._catalog = {s.screen_id: s for s in SCREEN_CATALOG}
        self._active_screen_id: ScreenId = ScreenId.HOME_DASHBOARD

    def get(self, screen_id: ScreenId) -> ScreenDescriptor | None:
        return self._catalog.get(screen_id)

    def navigate_to(self, screen_id: ScreenId) -> ScreenDescriptor:
        """Switch active screen, raising KeyError if invalid."""
        descriptor = self.get(screen_id)
        if descriptor is None:
            raise KeyError(f"screen {screen_id.value!r} not found in catalog")
        self._active_screen_id = screen_id
        return descriptor

    @property
    def active_screen(self) -> ScreenDescriptor:
        return self._catalog[self._active_screen_id]

    def all_screens(self) -> list[ScreenDescriptor]:
        return list(self._catalog.values())

    def by_category(self, category: ScreenCategory) -> list[ScreenDescriptor]:
        return [s for s in self._catalog.values() if s.category == category]


__all__ = [
    "SCREEN_CATALOG",
    "ScreenCatalogRegistry",
    "ScreenCategory",
    "ScreenDescriptor",
    "ScreenId",
]
