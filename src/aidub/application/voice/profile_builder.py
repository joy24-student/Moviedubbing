"""
Character Voice Profile Builder Service.

Assembles character voice profiles from mined dialogue references,
categorizing clips into emotion reference banks (Neutral, Angry, Sad, Whisper, Shout).
"""

from __future__ import annotations

import logging
from collections.abc import Sequence

from aidub.contracts.base import Identifier
from aidub.domain.voice_profile import (
    CharacterVoiceProfile,
    ReferenceBank,
    ReferenceQualityTier,
    ReferenceSample,
)

logger = logging.getLogger(__name__)


class CharacterVoiceProfileBuilder:
    """
    Service for constructing and managing character voice profiles and reference banks.
    """

    def build_character_profile(
        self,
        character_id: str,
        display_name: str,
        mined_references: Sequence[ReferenceSample],
        consent_authorized: bool = False,
    ) -> CharacterVoiceProfile:
        """
        Assemble character profile, partitioning references into emotion categories.
        """
        cid = Identifier(character_id)
        pid = Identifier(f"profile_{character_id}")

        banks: dict[str, ReferenceBank] = {}

        for ref in mined_references:
            if ref.quality_report.tier == ReferenceQualityTier.REJECTED:
                continue

            cat = ref.emotion_category.lower()
            if cat not in banks:
                banks[cat] = ReferenceBank(character_id=cid, emotion_category=cat, references=[])
            banks[cat].references.append(ref)

        # Select core embedding from best neutral reference if available
        core_emb = None
        if "neutral" in banks and banks["neutral"].references:
            best_ref = banks["neutral"].get_best_reference()
            if best_ref:
                core_emb = best_ref.embedding

        logger.info(
            "profile_builder: built profile %s for %s with %d reference banks (Consent: %s)",
            pid,
            display_name,
            len(banks),
            consent_authorized,
        )

        return CharacterVoiceProfile(
            profile_id=pid,
            character_id=cid,
            display_name=display_name,
            consent_authorized=consent_authorized,
            core_embedding=core_emb,
            reference_banks=banks,
        )


__all__ = [
    "CharacterVoiceProfileBuilder",
]
