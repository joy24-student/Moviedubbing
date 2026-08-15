"""
Dockable panel layout manager for saving/restoring custom desktop workspaces.

Presets:
  - EDITING: Default layout optimized for NLE timeline cuts.
  - DUBBING: Character, Voice, and Translation studio layout.
  - AUDIO_MIXING: Audio mixer, DSP chain, loudness meter layout.
  - QC: Subtitle studio & QC report validation layout.
"""

from __future__ import annotations

import logging
from enum import StrEnum

from pydantic import Field

from aidub.contracts.base import ContractModel, Identifier

logger = logging.getLogger(__name__)


class WorkspacePreset(StrEnum):
    EDITING = "editing"
    DUBBING = "dubbing"
    AUDIO_MIXING = "audio_mixing"
    QC = "qc"
    CUSTOM = "custom"


class PanelState(ContractModel):
    """Layout state of an individual dock panel."""

    panel_id: str = Field(min_length=1, max_length=64)
    visible: bool = True
    floating: bool = False
    width_px: int = Field(default=300, ge=100, le=4000)
    height_px: int = Field(default=600, ge=100, le=4000)
    dock_area: str = Field(default="left", max_length=32)


class WorkspaceLayout(ContractModel):
    """Complete window layout state snapshot."""

    layout_id: Identifier
    name: str = Field(min_length=1, max_length=128)
    preset: WorkspacePreset = WorkspacePreset.CUSTOM
    panels: list[PanelState] = Field(default_factory=list)
    active_screen_id: str = Field(default="home_dashboard", max_length=64)
    window_width_px: int = Field(default=1920, ge=800)
    window_height_px: int = Field(default=1080, ge=600)


_DEFAULT_PRESETS: dict[WorkspacePreset, list[PanelState]] = {
    WorkspacePreset.EDITING: [
        PanelState(panel_id="scene_browser", visible=True, dock_area="left", width_px=280),
        PanelState(panel_id="timeline_editor", visible=True, dock_area="center", height_px=400),
        PanelState(panel_id="dual_viewer", visible=True, dock_area="center", height_px=500),
        PanelState(panel_id="media_inspector", visible=True, dock_area="right", width_px=320),
    ],
    WorkspacePreset.DUBBING: [
        PanelState(panel_id="character_studio", visible=True, dock_area="left", width_px=320),
        PanelState(panel_id="translation_studio", visible=True, dock_area="center"),
        PanelState(panel_id="voice_studio", visible=True, dock_area="right", width_px=360),
    ],
    WorkspacePreset.AUDIO_MIXING: [
        PanelState(panel_id="audio_mixer", visible=True, dock_area="center"),
        PanelState(panel_id="dsp_chain", visible=True, dock_area="right", width_px=340),
        PanelState(panel_id="loudness_meter", visible=True, dock_area="right", width_px=280),
    ],
    WorkspacePreset.QC: [
        PanelState(panel_id="subtitle_studio", visible=True, dock_area="left", width_px=400),
        PanelState(panel_id="quality_control", visible=True, dock_area="center"),
        PanelState(panel_id="dual_viewer", visible=True, dock_area="right", width_px=600),
    ],
}


class WorkspaceManager:
    """
    Manages loading, saving, and restoring dock panel layouts.
    """

    def __init__(self) -> None:
        self._layouts: dict[str, WorkspaceLayout] = {}
        self._active_preset: WorkspacePreset = WorkspacePreset.EDITING

    def load_preset(self, preset: WorkspacePreset) -> WorkspaceLayout:
        """Load a predefined layout preset."""
        panels = _DEFAULT_PRESETS.get(preset, [])
        layout = WorkspaceLayout(
            layout_id=Identifier(f"layout_{preset.value}"),
            name=f"{preset.value.replace('_', ' ').title()} Workspace",
            preset=preset,
            panels=panels,
        )
        self._active_preset = preset
        logger.info("workspace_manager: loaded preset %s", preset.value)
        return layout

    def save_custom_layout(self, layout: WorkspaceLayout) -> None:
        """Save a custom workspace layout."""
        self._layouts[layout.layout_id] = layout
        logger.info("workspace_manager: saved custom layout %s", layout.name)

    def get_layout(self, layout_id: str) -> WorkspaceLayout | None:
        return self._layouts.get(layout_id)

    @property
    def active_preset(self) -> WorkspacePreset:
        return self._active_preset


__all__ = [
    "PanelState",
    "WorkspaceLayout",
    "WorkspaceManager",
    "WorkspacePreset",
]
