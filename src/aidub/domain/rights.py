"""Source authorization and responsible voice-use policy objects."""

from __future__ import annotations

from enum import StrEnum
from typing import Literal, Self

from pydantic import Field, model_validator

from .base import DomainModel, RightsViolation, UtcDatetime, utc_now
from .identifiers import ConsentRecordId, ProjectId, VoiceProfileId
from .types import LanguageTag, NonEmptyStr, TerritoryCode


class SourceAuthorization(DomainModel):
    """Recorded operator assertion that source media may be processed."""

    acknowledged: Literal[True]
    acknowledged_by: NonEmptyStr
    acknowledged_at: UtcDatetime = Field(default_factory=utc_now)
    authority_basis: NonEmptyStr
    evidence_reference: NonEmptyStr | None = None


class ConsentStatus(StrEnum):
    PENDING = "pending"
    GRANTED = "granted"
    REVOKED = "revoked"


class VoiceUse(StrEnum):
    DUBBING = "dubbing"
    PREVIEW = "preview"
    FINAL_EXPORT = "final_export"
    PROMOTION = "promotion"
    MODEL_TRAINING = "model_training"


class VoiceOrigin(StrEnum):
    SYNTHETIC_STOCK = "synthetic_stock"
    LICENSED_LIBRARY = "licensed_library"
    REFERENCE_CONDITIONED = "reference_conditioned"
    CLONED = "cloned"
    ORIGINAL_PERFORMER = "original_performer"


class VoiceProfileStatus(StrEnum):
    ACTIVE = "active"
    DISABLED = "disabled"


class ConsentRecord(DomainModel):
    """Auditable grant governing a voice subject or licensor's permitted uses."""

    consent_record_id: ConsentRecordId
    project_id: ProjectId | None = None
    subject: NonEmptyStr
    rights_owner: NonEmptyStr
    status: ConsentStatus
    evidence_reference: NonEmptyStr | None = None
    permitted_uses: frozenset[VoiceUse] = frozenset()
    languages: frozenset[LanguageTag | Literal["*"]] = frozenset()
    territories: frozenset[TerritoryCode] = frozenset()
    valid_from: UtcDatetime | None = None
    expires_at: UtcDatetime | None = None
    approved_by: NonEmptyStr | None = None
    approved_at: UtcDatetime | None = None
    revoked_at: UtcDatetime | None = None
    revocation_reason: NonEmptyStr | None = None
    notes: str = Field(default="", max_length=10_000)

    @model_validator(mode="after")
    def _validate_lifecycle(self) -> Self:
        if (
            self.expires_at is not None
            and self.valid_from is not None
            and self.expires_at <= self.valid_from
        ):
            raise ValueError("consent expiry must follow its valid-from timestamp")

        if self.status is ConsentStatus.GRANTED:
            missing = []
            if self.evidence_reference is None:
                missing.append("evidence_reference")
            if not self.permitted_uses:
                missing.append("permitted_uses")
            if not self.languages:
                missing.append("languages")
            if not self.territories:
                missing.append("territories")
            if self.approved_by is None:
                missing.append("approved_by")
            if self.approved_at is None:
                missing.append("approved_at")
            if missing:
                raise ValueError(f"granted consent is missing: {', '.join(missing)}")
            if self.revoked_at is not None:
                raise ValueError("granted consent cannot have a revocation timestamp")

        if self.status is ConsentStatus.REVOKED:
            if self.revoked_at is None or self.revocation_reason is None:
                raise ValueError("revoked consent requires time and reason")
            if self.approved_at is not None and self.revoked_at < self.approved_at:
                raise ValueError("consent cannot be revoked before it was approved")
        elif self.revoked_at is not None or self.revocation_reason is not None:
            raise ValueError("only revoked consent may carry revocation details")
        return self

    def permits(
        self,
        *,
        language: str,
        territory: str,
        use: VoiceUse,
        at: UtcDatetime,
    ) -> bool:
        """Return whether this grant authorizes a use at a specific instant."""

        if self.status is not ConsentStatus.GRANTED:
            return False
        # DomainModel normalizes persisted datetimes; normalize request time through a tiny model
        # boundary so naive timestamps are rejected consistently.
        instant = _UseInstant(at=at).at
        if self.valid_from is not None and instant < self.valid_from:
            return False
        if self.expires_at is not None and instant >= self.expires_at:
            return False
        language_allowed = "*" in self.languages or language in self.languages
        territory_allowed = "WORLDWIDE" in self.territories or territory in self.territories
        return language_allowed and territory_allowed and use in self.permitted_uses


class _UseInstant(DomainModel):
    at: UtcDatetime


class VoiceProfile(DomainModel):
    """Editorial voice configuration, separate from generated takes."""

    voice_profile_id: VoiceProfileId
    project_id: ProjectId
    display_name: NonEmptyStr
    origin: VoiceOrigin
    status: VoiceProfileStatus = VoiceProfileStatus.ACTIVE
    engine_id: NonEmptyStr
    engine_voice_key: NonEmptyStr
    supported_languages: frozenset[LanguageTag | Literal["*"]]
    consent_record_id: ConsentRecordId | None = None
    reference_artifact_ids: tuple[str, ...] = ()

    @model_validator(mode="after")
    def _require_license_or_consent(self) -> Self:
        controlled_origins = {
            VoiceOrigin.LICENSED_LIBRARY,
            VoiceOrigin.REFERENCE_CONDITIONED,
            VoiceOrigin.CLONED,
            VoiceOrigin.ORIGINAL_PERFORMER,
        }
        if self.origin in controlled_origins and self.consent_record_id is None:
            raise ValueError(f"{self.origin.value} voice requires a consent/license record")
        if not self.supported_languages:
            raise ValueError("voice profile must support at least one language")
        if len(set(self.reference_artifact_ids)) != len(self.reference_artifact_ids):
            raise ValueError("reference artifact identifiers must be unique")
        return self


class VoiceUsageRequest(DomainModel):
    project_id: ProjectId
    voice_profile_id: VoiceProfileId
    language: LanguageTag
    territory: TerritoryCode
    use: VoiceUse
    requested_at: UtcDatetime = Field(default_factory=utc_now)


def assert_voice_use_authorized(
    profile: VoiceProfile,
    consent: ConsentRecord | None,
    request: VoiceUsageRequest,
) -> None:
    """Reject generation/export that is disabled, mismatched, expired, or revoked."""

    if (
        profile.project_id != request.project_id
        or profile.voice_profile_id != request.voice_profile_id
    ):
        raise RightsViolation("voice usage request does not match the selected profile")
    if profile.status is not VoiceProfileStatus.ACTIVE:
        raise RightsViolation("voice profile is disabled")
    if (
        request.language not in profile.supported_languages
        and "*" not in profile.supported_languages
    ):
        raise RightsViolation("voice profile does not support the requested language")

    if profile.origin is VoiceOrigin.SYNTHETIC_STOCK and profile.consent_record_id is None:
        return
    if consent is None or profile.consent_record_id != consent.consent_record_id:
        raise RightsViolation("voice profile has no matching consent/license record")
    if consent.project_id is not None and consent.project_id != request.project_id:
        raise RightsViolation("consent/license record belongs to another project")
    if not consent.permits(
        language=request.language,
        territory=request.territory,
        use=request.use,
        at=request.requested_at,
    ):
        raise RightsViolation("voice use is outside the active consent/license grant")


__all__ = [
    "ConsentRecord",
    "ConsentStatus",
    "SourceAuthorization",
    "VoiceOrigin",
    "VoiceProfile",
    "VoiceProfileStatus",
    "VoiceUsageRequest",
    "VoiceUse",
    "assert_voice_use_authorized",
]
