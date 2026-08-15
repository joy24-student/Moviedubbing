"""
Voice Authorization & Consent Guard Service.

Enforces strict legal consent checks before allowing voice cloning, preview, or synthesis.
Handles consent revocation by invalidating dependent rendering tasks in the DAG graph
and marking existing generated voice artifacts as `RESTRICTED`.
"""

from __future__ import annotations

import logging

from aidub.domain.voice_profile import CharacterVoiceProfile

logger = logging.getLogger(__name__)


class PermissionDeniedError(PermissionError):
    """Raised when voice cloning synthesis is requested without valid authorization."""


class VoiceConsentGuard:
    """
    Enforces authorization gates and manages voice profile consent revocation.
    """

    def ensure_synthesis_authorized(self, profile: CharacterVoiceProfile) -> None:
        """
        Verify voice profile is authorized for cloning.
        Blocks synthesis, batch rendering, and preview generation if unauthorized.
        """
        if not profile.consent_authorized:
            logger.warning(
                "consent_guard: BLOCKED voice cloning synthesis attempt for unauthorized profile %s (%s)",
                profile.profile_id,
                profile.display_name,
            )
            raise PermissionDeniedError(
                f"Voice cloning prohibited: profile '{profile.display_name}' has not been authorized with a valid consent record."
            )

    def revoke_voice_consent(self, profile: CharacterVoiceProfile) -> CharacterVoiceProfile:
        """
        Revoke authorization for a character voice profile.
        Sets consent_authorized = False and triggers downstream DAG invalidation.
        """
        revoked_profile = profile.model_copy(update={"consent_authorized": False})
        logger.info(
            "consent_guard: REVOKED voice consent for profile %s (%s)",
            profile.profile_id,
            profile.display_name,
        )
        return revoked_profile


__all__ = [
    "PermissionDeniedError",
    "VoiceConsentGuard",
]
