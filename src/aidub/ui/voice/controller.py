"""
Voice Cloning Studio Presentation UI Controller.

Manages Python business logic bindings, reference quality ranking, consent status audits,
and take evaluation preview triggers for the QML / Qt Quick presentation layer.
"""

from __future__ import annotations

import logging
from collections.abc import Sequence

from aidub.application.voice.consent_guard import VoiceConsentGuard
from aidub.application.voice.profile_builder import CharacterVoiceProfileBuilder
from aidub.application.voice.take_evaluator import VoiceTakeEvaluator, VoiceTakeQcReport
from aidub.domain.voice_profile import CharacterVoiceProfile, ReferenceSample

logger = logging.getLogger(__name__)


class VoiceCloningStudioController:
    """
    Controller binding business logic to Qt Quick QML views (headless safe).
    """

    def __init__(self) -> None:
        self.profile_builder = CharacterVoiceProfileBuilder()
        self.consent_guard = VoiceConsentGuard()
        self.take_evaluator = VoiceTakeEvaluator()
        self.active_profile: CharacterVoiceProfile | None = None

    def load_character_profile(
        self,
        character_id: str,
        display_name: str,
        mined_references: Sequence[ReferenceSample],
        consent_authorized: bool = False,
    ) -> CharacterVoiceProfile:
        """
        Load or assemble character profile.
        """
        self.active_profile = self.profile_builder.build_character_profile(
            character_id, display_name, mined_references, consent_authorized
        )
        return self.active_profile

    def authorize_consent(self) -> bool:
        """
        Grant consent authorization for active character profile.
        """
        if not self.active_profile:
            return False
        self.active_profile = self.active_profile.model_copy(update={"consent_authorized": True})
        logger.info("voice_controller: authorized consent for %s", self.active_profile.character_id)
        return True

    def revoke_consent(self) -> bool:
        """
        Revoke consent authorization for active character profile.
        """
        if not self.active_profile:
            return False
        self.active_profile = self.consent_guard.revoke_voice_consent(self.active_profile)
        return True

    def request_synthesis_preview(self, utterance_id: str, target_language: str = "bn-BD") -> str:
        """
        Check authorization and generate synthesis preview request token.
        """
        if not self.active_profile:
            raise ValueError("No active voice profile loaded")

        # Enforce consent guard gate
        self.consent_guard.ensure_synthesis_authorized(self.active_profile)

        preview_token = f"preview_{self.active_profile.character_id}_{utterance_id}_{target_language}"
        logger.info("voice_controller: generated synthesis preview token %s", preview_token)
        return preview_token

    def evaluate_synthesized_take(
        self,
        take_id: str,
        utterance_id: str,
        speaker_similarity: float = 0.92,
    ) -> VoiceTakeQcReport:
        """
        Evaluate quality metrics for a synthesized take.
        """
        return self.take_evaluator.evaluate_take(
            take_id=take_id,
            utterance_id=utterance_id,
            speaker_similarity=speaker_similarity,
        )


__all__ = [
    "VoiceCloningStudioController",
]
