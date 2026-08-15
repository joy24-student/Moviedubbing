-- Durable, revision-safe transcript snapshots and mutation facts.
-- The canonical aggregate remains JSON so domain validation evolves independently
-- of SQLite column layout; revision and scope fields remain first-class for CAS.

CREATE TABLE transcript_snapshots (
    project_id TEXT NOT NULL REFERENCES projects(id) ON UPDATE CASCADE ON DELETE RESTRICT,
    media_asset_id TEXT NOT NULL CHECK (length(media_asset_id) > 0),
    language TEXT NOT NULL COLLATE NOCASE CHECK (length(trim(language)) > 0),
    revision INTEGER NOT NULL CHECK (revision >= 0),
    transcript_json TEXT NOT NULL CHECK (json_valid(transcript_json)),
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    PRIMARY KEY (project_id, media_asset_id, language)
);

CREATE TABLE transcript_mutations (
    project_id TEXT NOT NULL,
    media_asset_id TEXT NOT NULL,
    language TEXT NOT NULL COLLATE NOCASE,
    revision INTEGER NOT NULL CHECK (revision > 0),
    operation TEXT NOT NULL CHECK (length(operation) > 0),
    actor TEXT NOT NULL CHECK (length(trim(actor)) > 0),
    automated INTEGER NOT NULL CHECK (automated IN (0, 1)),
    occurred_at TEXT NOT NULL,
    affected_utterance_ids_json TEXT NOT NULL CHECK (json_valid(affected_utterance_ids_json)),
    invalidation_roots_json TEXT NOT NULL CHECK (json_valid(invalidation_roots_json)),
    transcript_sha256 TEXT NOT NULL CHECK (
        length(transcript_sha256) = 64
        AND transcript_sha256 NOT GLOB '*[^0-9a-f]*'
    ),
    PRIMARY KEY (project_id, media_asset_id, language, revision),
    FOREIGN KEY (project_id, media_asset_id, language)
        REFERENCES transcript_snapshots(project_id, media_asset_id, language)
        ON UPDATE CASCADE ON DELETE RESTRICT
);

CREATE INDEX idx_transcript_mutations_project_time
    ON transcript_mutations(project_id, occurred_at, revision);

CREATE TRIGGER transcript_mutations_no_update
BEFORE UPDATE ON transcript_mutations
BEGIN
    SELECT RAISE(ABORT, 'transcript mutations are append-only');
END;

CREATE TRIGGER transcript_mutations_no_delete
BEFORE DELETE ON transcript_mutations
BEGIN
    SELECT RAISE(ABORT, 'transcript mutations are append-only');
END;
