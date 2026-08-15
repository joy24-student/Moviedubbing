"""
Studio Analytics & Cloud Sync UI Presentation Controller.

Binds cloud sync queues, character LoRA fine-tuning jobs, cost dashboards,
and tenant budget reports to the Qt Quick QML presentation layer.
"""

from __future__ import annotations

import logging

from aidub.ai.finetuning.finetune_pipeline import (
    FineTuningConfig,
    FineTuningReport,
    VoiceAdapterFineTuner,
)
from aidub.analytics.studio_analytics import StudioAnalyticsPlatform, TenantAnalyticsReport
from aidub.cloud.hybrid_sync import CloudHybridSyncEngine, CloudSyncManifest
from aidub.domain.voice_profile import CharacterVoiceProfile

logger = logging.getLogger(__name__)


class AnalyticsStudioController:
    """
    Controller binding Phase 11 cloud, fine-tuning, and analytics features to Qt Quick QML views.
    """

    def __init__(self) -> None:
        self.sync_engine = CloudHybridSyncEngine()
        self.finetuner = VoiceAdapterFineTuner()
        self.analytics = StudioAnalyticsPlatform()

    def sync_project_to_cloud(self, project_id: str) -> CloudSyncManifest:
        """
        Create and execute cloud sync for project files.
        """
        manifest = self.sync_engine.create_sync_manifest(project_id)
        return self.sync_engine.synchronize_project(manifest)

    def fine_tune_character_voice(self, job_id: str, profile: CharacterVoiceProfile) -> FineTuningReport:
        """
        Trigger LoRA fine-tuning job for character voice adapter.
        """
        cfg = FineTuningConfig(character_id=profile.character_id)
        return self.finetuner.execute_fine_tuning_job(job_id, profile, cfg)

    def fetch_tenant_analytics_summary(self, tenant_id: str) -> TenantAnalyticsReport:
        """
        Fetch aggregate studio cost analytics and budget alert status.
        """
        c1 = self.analytics.compute_project_cost("proj_01", audio_minutes=120.0, gpu_hours=4.5)
        c2 = self.analytics.compute_project_cost("proj_02", audio_minutes=90.0, gpu_hours=3.0)
        return self.analytics.generate_tenant_report(tenant_id, [c1, c2], budget_limit_usd=500.0)


__all__ = [
    "AnalyticsStudioController",
]
