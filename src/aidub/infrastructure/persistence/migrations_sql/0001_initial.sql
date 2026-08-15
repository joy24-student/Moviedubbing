-- AI Dubbing Studio project schema v1.
-- Binary payloads are intentionally excluded; artifacts contain only catalog data.

CREATE TABLE schema_version (
    version INTEGER PRIMARY KEY CHECK (version > 0),
    name TEXT NOT NULL CHECK (length(name) > 0),
    checksum TEXT NOT NULL CHECK (
        length(checksum) = 64 AND checksum NOT GLOB '*[^0-9a-f]*'
    ),
    applied_at TEXT NOT NULL
);

CREATE TABLE projects (
    id TEXT PRIMARY KEY CHECK (length(id) > 0),
    name TEXT NOT NULL CHECK (length(trim(name)) > 0),
    source_language TEXT,
    settings_json TEXT NOT NULL DEFAULT '{}' CHECK (json_valid(settings_json)),
    state TEXT NOT NULL DEFAULT 'ACTIVE' CHECK (
        state IN ('ACTIVE', 'ARCHIVED', 'READ_ONLY', 'RECOVERY_REQUIRED')
    ),
    revision INTEGER NOT NULL DEFAULT 0 CHECK (revision >= 0),
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE jobs (
    id TEXT PRIMARY KEY CHECK (length(id) > 0),
    project_id TEXT NOT NULL REFERENCES projects(id) ON UPDATE CASCADE ON DELETE RESTRICT,
    job_type TEXT NOT NULL CHECK (length(job_type) > 0),
    idempotency_key TEXT NOT NULL CHECK (length(idempotency_key) > 0),
    state TEXT NOT NULL CHECK (
        state IN (
            'QUEUED', 'BLOCKED', 'PREPARING', 'RUNNING', 'PAUSING', 'PAUSED',
            'CANCELLING', 'CANCELLED', 'FAILED', 'SUCCEEDED', 'STALE'
        )
    ),
    priority INTEGER NOT NULL DEFAULT 0,
    progress REAL NOT NULL DEFAULT 0.0 CHECK (progress >= 0.0 AND progress <= 1.0),
    scope_json TEXT NOT NULL DEFAULT '{}' CHECK (json_valid(scope_json)),
    input_json TEXT NOT NULL DEFAULT '{}' CHECK (json_valid(input_json)),
    expected_output_json TEXT NOT NULL DEFAULT '{}' CHECK (json_valid(expected_output_json)),
    resource_request_json TEXT NOT NULL DEFAULT '{}' CHECK (json_valid(resource_request_json)),
    checkpoint_json TEXT CHECK (checkpoint_json IS NULL OR json_valid(checkpoint_json)),
    retry_count INTEGER NOT NULL DEFAULT 0 CHECK (retry_count >= 0),
    max_retries INTEGER NOT NULL DEFAULT 0 CHECK (max_retries >= 0),
    error_category TEXT,
    error_message TEXT,
    lease_owner TEXT,
    lease_expires_at TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    started_at TEXT,
    completed_at TEXT,
    UNIQUE (project_id, idempotency_key)
);

CREATE TABLE job_dependencies (
    job_id TEXT NOT NULL REFERENCES jobs(id) ON UPDATE CASCADE ON DELETE CASCADE,
    depends_on_job_id TEXT NOT NULL REFERENCES jobs(id) ON UPDATE CASCADE ON DELETE RESTRICT,
    PRIMARY KEY (job_id, depends_on_job_id),
    CHECK (job_id <> depends_on_job_id)
);

CREATE TABLE artifacts (
    id TEXT PRIMARY KEY CHECK (length(id) > 0),
    project_id TEXT NOT NULL REFERENCES projects(id) ON UPDATE CASCADE ON DELETE RESTRICT,
    sha256 TEXT NOT NULL CHECK (
        length(sha256) = 64 AND sha256 NOT GLOB '*[^0-9a-f]*'
    ),
    byte_length INTEGER NOT NULL CHECK (byte_length >= 0),
    relative_path TEXT NOT NULL CHECK (
        length(relative_path) > 0
        AND relative_path NOT LIKE '/%'
        AND relative_path NOT LIKE '\%'
        AND instr(relative_path, '..') = 0
    ),
    logical_type TEXT NOT NULL CHECK (length(logical_type) > 0),
    media_type TEXT,
    status TEXT NOT NULL DEFAULT 'READY' CHECK (
        status IN ('READY', 'MISSING', 'CORRUPT', 'QUARANTINED')
    ),
    metadata_json TEXT NOT NULL DEFAULT '{}' CHECK (json_valid(metadata_json)),
    engine_id TEXT,
    engine_version TEXT,
    model_id TEXT,
    model_version TEXT,
    model_weight_sha256 TEXT CHECK (
        model_weight_sha256 IS NULL OR (
            length(model_weight_sha256) = 64
            AND model_weight_sha256 NOT GLOB '*[^0-9a-f]*'
        )
    ),
    parameters_json TEXT NOT NULL DEFAULT '{}' CHECK (json_valid(parameters_json)),
    prompt_version TEXT,
    provider_id TEXT,
    hardware_json TEXT NOT NULL DEFAULT '{}' CHECK (json_valid(hardware_json)),
    quality_metrics_json TEXT NOT NULL DEFAULT '{}' CHECK (json_valid(quality_metrics_json)),
    seed INTEGER,
    reproducibility_level TEXT NOT NULL DEFAULT 'BEST_EFFORT' CHECK (
        reproducibility_level IN ('EXACT', 'BEST_EFFORT', 'NON_REPRODUCIBLE')
    ),
    created_by TEXT,
    created_at TEXT NOT NULL,
    UNIQUE (project_id, sha256, logical_type)
);

CREATE TABLE artifact_dependencies (
    artifact_id TEXT NOT NULL REFERENCES artifacts(id) ON UPDATE CASCADE ON DELETE CASCADE,
    source_artifact_id TEXT NOT NULL REFERENCES artifacts(id) ON UPDATE CASCADE ON DELETE RESTRICT,
    dependency_role TEXT NOT NULL DEFAULT 'input',
    ordinal INTEGER NOT NULL DEFAULT 0 CHECK (ordinal >= 0),
    PRIMARY KEY (artifact_id, source_artifact_id, dependency_role),
    CHECK (artifact_id <> source_artifact_id)
);

CREATE TABLE audit_events (
    id TEXT PRIMARY KEY CHECK (length(id) > 0),
    project_id TEXT NOT NULL REFERENCES projects(id) ON UPDATE CASCADE ON DELETE RESTRICT,
    occurred_at TEXT NOT NULL,
    actor_type TEXT NOT NULL CHECK (length(actor_type) > 0),
    actor_id TEXT,
    action TEXT NOT NULL CHECK (length(action) > 0),
    target_type TEXT,
    target_id TEXT,
    job_id TEXT REFERENCES jobs(id) ON UPDATE CASCADE ON DELETE SET NULL,
    artifact_id TEXT REFERENCES artifacts(id) ON UPDATE CASCADE ON DELETE SET NULL,
    correlation_id TEXT,
    details_json TEXT NOT NULL DEFAULT '{}' CHECK (json_valid(details_json))
);

