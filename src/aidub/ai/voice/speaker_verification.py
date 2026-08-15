"""
Post-Synthesis Speaker Verification Engine.

Calculates post-synthesis speaker similarity scores by extracting speaker embeddings
from generated voice takes and comparing cosine distance against reference voice profiles.
"""

from __future__ import annotations

import logging

from aidub.domain.speaker_embedding import SpeakerEmbedding

logger = logging.getLogger(__name__)


class SpeakerVerificationEngine:
    """
    Computes speaker similarity verification metrics between synthesized voice takes and reference profiles.
    """

    def verify_speaker_similarity(
        self,
        reference_embedding: SpeakerEmbedding,
        synthesized_embedding: SpeakerEmbedding,
    ) -> float:
        """
        Compute cosine similarity score between reference and synthesized speaker embeddings.
        """
        similarity = reference_embedding.compute_cosine_similarity(synthesized_embedding)
        logger.info(
            "speaker_verification: computed similarity %.4f between reference (%s) and synthesis (%s)",
            similarity,
            reference_embedding.model_id,
            synthesized_embedding.model_id,
        )
        return similarity


__all__ = [
    "SpeakerVerificationEngine",
]
