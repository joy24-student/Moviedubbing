"""Atomic storage for immutable transcript snapshots and mutation evidence."""

from __future__ import annotations

import hashlib
import json
import sqlite3
from dataclasses import dataclass

from aidub.infrastructure.persistence import ProjectDatabase
from aidub.infrastructure.persistence.models import utc_now
from aidub.transcript import (
    InvalidationRoot,
    Transcript,
    TranscriptAuditFact,
    TranscriptMutationResult,
    TranscriptOperation,
)

from .errors import (
    StoredTranscriptNotFoundError,
    StoredTranscriptRevisionConflict,
    TranscriptAlreadyExistsError,
    TranscriptPersistenceInvariantError,
)


def _canonical_json(value: object) -> str:
    return json.dumps(
        value,
        allow_nan=False,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    )


def _transcript_json(transcript: Transcript) -> str:
    return _canonical_json(transcript.model_dump(mode="json"))


def _sha256(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _decode_json(value: str, *, field: str) -> object:
    try:
        return json.loads(value)
    except json.JSONDecodeError as error:
        raise TranscriptPersistenceInvariantError(
            f"stored {field} contains invalid JSON"
        ) from error


@dataclass(frozen=True, slots=True)
class PersistedTranscriptMutation:
    """Append-only evidence that one validated aggregate revision was committed."""

    audit: TranscriptAuditFact
    invalidation_roots: tuple[InvalidationRoot, ...]
    transcript_sha256: str


class TranscriptStore:
    """Durable compare-and-swap repository over a project's SQLite database.

    Domain commands stay pure: callers load a snapshot, use
    ``TranscriptCommandService``, then persist the returned mutation result. The
    store checks the source revision again inside a single immediate transaction,
    so a stale editor cannot overwrite a newer edit.
    """

    def __init__(self, database: ProjectDatabase) -> None:
        self._database = database

    def create(self, transcript: Transcript) -> Transcript:
        """Persist the initial revision-zero snapshot exactly once."""

        if transcript.revision != 0:
            raise TranscriptPersistenceInvariantError(
                "an initial transcript snapshot must use revision zero"
            )
        payload = _transcript_json(transcript)
        timestamp = utc_now()
        try:
            with self._database.transaction() as connection:
                connection.execute(
                    "INSERT INTO transcript_snapshots("
                    "project_id, media_asset_id, language, revision, transcript_json, "
                    "created_at, updated_at"
                    ") VALUES (?, ?, ?, ?, ?, ?, ?)",
                    (
                        transcript.project_id,
                        transcript.media_asset_id,
                        transcript.language,
                        transcript.revision,
                        payload,
                        timestamp,
                        timestamp,
                    ),
                )
        except sqlite3.IntegrityError as error:
            if "UNIQUE constraint failed: transcript_snapshots" in str(error):
                raise TranscriptAlreadyExistsError(
                    "a transcript already exists for this project/media/language scope"
                ) from error
            raise
        return transcript

    def get(self, *, project_id: str, media_asset_id: str, language: str) -> Transcript | None:
        """Load the latest validated aggregate snapshot, if it exists."""

        with self._database.connection() as connection:
            row = connection.execute(
                "SELECT transcript_json FROM transcript_snapshots "
                "WHERE project_id = ? AND media_asset_id = ? AND language = ?",
                (project_id, media_asset_id, language),
            ).fetchone()
        if row is None:
            return None
        try:
            return Transcript.model_validate_json(str(row["transcript_json"]))
        except ValueError as error:
            raise TranscriptPersistenceInvariantError(
                "stored transcript does not satisfy current domain validation"
            ) from error

    def require(self, *, project_id: str, media_asset_id: str, language: str) -> Transcript:
        """Load one transcript or raise a scoped absence error."""

        transcript = self.get(
            project_id=project_id,
            media_asset_id=media_asset_id,
            language=language,
        )
        if transcript is None:
            raise StoredTranscriptNotFoundError(
                "no transcript exists for the requested project/media/language scope"
            )
        return transcript

    def commit(self, result: TranscriptMutationResult) -> TranscriptMutationResult:
        """Atomically publish a next revision plus append-only mutation evidence."""

        transcript = result.transcript
        audit = result.audit
        self._validate_commit_scope(result)
        payload = _transcript_json(transcript)
        payload_sha256 = _sha256(payload)
        affected_ids = _canonical_json(list(audit.affected_utterance_ids))
        roots = _canonical_json(
            [root.model_dump(mode="json") for root in result.invalidation_roots]
        )
        timestamp = utc_now()

        with self._database.transaction() as connection:
            row = connection.execute(
                "SELECT revision FROM transcript_snapshots "
                "WHERE project_id = ? AND media_asset_id = ? AND language = ?",
                (transcript.project_id, transcript.media_asset_id, transcript.language),
            ).fetchone()
            if row is None:
                raise StoredTranscriptNotFoundError(
                    "cannot commit a mutation for a transcript that does not exist"
                )
            actual_revision = int(row["revision"])
            if actual_revision != audit.expected_revision:
                raise StoredTranscriptRevisionConflict(
                    f"transcript revision conflict: expected {audit.expected_revision}, "
                    f"stored {actual_revision}"
                )
            cursor = connection.execute(
                "UPDATE transcript_snapshots SET revision = ?, transcript_json = ?, updated_at = ? "
                "WHERE project_id = ? AND media_asset_id = ? AND language = ? AND revision = ?",
                (
                    transcript.revision,
                    payload,
                    timestamp,
                    transcript.project_id,
                    transcript.media_asset_id,
                    transcript.language,
                    audit.expected_revision,
                ),
            )
            if cursor.rowcount != 1:
                raise StoredTranscriptRevisionConflict(
                    "transcript changed before the requested mutation could be committed"
                )
            connection.execute(
                "INSERT INTO transcript_mutations("
                "project_id, media_asset_id, language, revision, operation, actor, automated, "
                "occurred_at, affected_utterance_ids_json, invalidation_roots_json, "
                "transcript_sha256"
                ") VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    transcript.project_id,
                    transcript.media_asset_id,
                    transcript.language,
                    audit.new_revision,
                    audit.operation.value,
                    audit.actor,
                    int(audit.automated),
                    audit.occurred_at.isoformat().replace("+00:00", "Z"),
                    affected_ids,
                    roots,
                    payload_sha256,
                ),
            )
        return result

    def history(
        self,
        *,
        project_id: str,
        media_asset_id: str,
        language: str,
        limit: int = 1_000,
    ) -> tuple[PersistedTranscriptMutation, ...]:
        """Return append-only mutation evidence ordered by aggregate revision."""

        if limit <= 0:
            raise ValueError("limit must be positive")
        with self._database.connection() as connection:
            rows = connection.execute(
                "SELECT revision, operation, actor, automated, occurred_at, "
                "affected_utterance_ids_json, invalidation_roots_json, transcript_sha256 "
                "FROM transcript_mutations WHERE project_id = ? AND media_asset_id = ? "
                "AND language = ? ORDER BY revision LIMIT ?",
                (project_id, media_asset_id, language, limit),
            ).fetchall()
        return tuple(self._mutation_from_row(row) for row in rows)

    @staticmethod
    def _validate_commit_scope(result: TranscriptMutationResult) -> None:
        transcript = result.transcript
        audit = result.audit
        if transcript.revision != audit.new_revision:
            raise TranscriptPersistenceInvariantError(
                "committed transcript revision must equal the audit fact's new revision"
            )
        if audit.new_revision != audit.expected_revision + 1:
            raise TranscriptPersistenceInvariantError("mutation revisions must be consecutive")
        known_ids = {line.utterance_id for line in transcript.utterances}
        for root in result.invalidation_roots:
            if (
                root.project_id != transcript.project_id
                or root.media_asset_id != transcript.media_asset_id
                or root.language.casefold() != transcript.language.casefold()
            ):
                raise TranscriptPersistenceInvariantError(
                    "invalidation roots must use the committed transcript scope"
                )
            if (
                root.utterance_id not in known_ids
                and root.utterance_id not in audit.affected_utterance_ids
            ):
                raise TranscriptPersistenceInvariantError(
                    "an invalidation root must reference a current or affected utterance"
                )

    @staticmethod
    def _mutation_from_row(row: sqlite3.Row) -> PersistedTranscriptMutation:
        affected = _decode_json(
            str(row["affected_utterance_ids_json"]), field="affected utterance IDs"
        )
        roots = _decode_json(str(row["invalidation_roots_json"]), field="invalidation roots")
        if not isinstance(affected, list) or not all(isinstance(item, str) for item in affected):
            raise TranscriptPersistenceInvariantError(
                "stored affected utterance IDs must be a JSON array of strings"
            )
        if not isinstance(roots, list) or not all(isinstance(item, dict) for item in roots):
            raise TranscriptPersistenceInvariantError(
                "stored invalidation roots must be a JSON array of objects"
            )
        try:
            audit = TranscriptAuditFact.model_validate_json(
                _canonical_json(
                    {
                        "operation": TranscriptOperation(str(row["operation"])),
                        "actor": str(row["actor"]),
                        "occurred_at": str(row["occurred_at"]),
                        "expected_revision": int(row["revision"]) - 1,
                        "new_revision": int(row["revision"]),
                        "affected_utterance_ids": affected,
                        "automated": bool(row["automated"]),
                    }
                )
            )
            invalidation_roots = tuple(
                InvalidationRoot.model_validate_json(_canonical_json(item)) for item in roots
            )
        except ValueError as error:
            raise TranscriptPersistenceInvariantError(
                "stored transcript mutation does not satisfy current domain validation"
            ) from error
        return PersistedTranscriptMutation(
            audit=audit,
            invalidation_roots=invalidation_roots,
            transcript_sha256=str(row["transcript_sha256"]),
        )


__all__ = ["PersistedTranscriptMutation", "TranscriptStore"]
