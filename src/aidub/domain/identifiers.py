"""Stable, externally serializable identifiers used by domain schemas."""

from __future__ import annotations

from typing import Annotated, TypeAlias
from uuid import uuid4

from pydantic import StringConstraints

ProjectId: TypeAlias = Annotated[
    str, StringConstraints(pattern=r"^prj_[A-Za-z0-9][A-Za-z0-9_-]{2,63}$")
]
MediaAssetId: TypeAlias = Annotated[
    str, StringConstraints(pattern=r"^med_[A-Za-z0-9][A-Za-z0-9_-]{2,63}$")
]
LocalizationId: TypeAlias = Annotated[
    str, StringConstraints(pattern=r"^loc_[A-Za-z0-9][A-Za-z0-9_-]{2,63}$")
]
UtteranceId: TypeAlias = Annotated[
    str, StringConstraints(pattern=r"^utt_[A-Za-z0-9][A-Za-z0-9_-]{2,63}$")
]
SceneId: TypeAlias = Annotated[
    str, StringConstraints(pattern=r"^scn_[A-Za-z0-9][A-Za-z0-9_-]{2,63}$")
]
SpeakerId: TypeAlias = Annotated[
    str, StringConstraints(pattern=r"^spk_[A-Za-z0-9][A-Za-z0-9_-]{2,63}$")
]
CharacterId: TypeAlias = Annotated[
    str, StringConstraints(pattern=r"^(?:chr|char)_[A-Za-z0-9][A-Za-z0-9_-]{2,63}$")
]
TranslationVersionId: TypeAlias = Annotated[
    str, StringConstraints(pattern=r"^trn_[A-Za-z0-9][A-Za-z0-9_-]{2,63}$")
]
VoiceProfileId: TypeAlias = Annotated[
    str, StringConstraints(pattern=r"^vcp_[A-Za-z0-9][A-Za-z0-9_-]{2,63}$")
]
ConsentRecordId: TypeAlias = Annotated[
    str, StringConstraints(pattern=r"^cns_[A-Za-z0-9][A-Za-z0-9_-]{2,63}$")
]
ArtifactId: TypeAlias = Annotated[
    str, StringConstraints(pattern=r"^art_[A-Za-z0-9][A-Za-z0-9_-]{2,63}$")
]
JobId: TypeAlias = Annotated[
    str, StringConstraints(pattern=r"^job_[A-Za-z0-9][A-Za-z0-9_-]{2,63}$")
]

_KNOWN_PREFIXES = frozenset(
    {"prj", "med", "loc", "utt", "scn", "spk", "chr", "char", "trn", "vcp", "cns", "art", "job"}
)


def new_id(prefix: str) -> str:
    """Create a collision-resistant domain identifier with an approved prefix."""

    if prefix not in _KNOWN_PREFIXES:
        raise ValueError(f"unsupported identifier prefix: {prefix!r}")
    return f"{prefix}_{uuid4().hex}"


__all__ = [
    "ArtifactId",
    "CharacterId",
    "ConsentRecordId",
    "JobId",
    "LocalizationId",
    "MediaAssetId",
    "ProjectId",
    "SceneId",
    "SpeakerId",
    "TranslationVersionId",
    "UtteranceId",
    "VoiceProfileId",
    "new_id",
]
