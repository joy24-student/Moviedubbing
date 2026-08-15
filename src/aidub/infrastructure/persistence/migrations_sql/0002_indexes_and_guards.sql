-- Query indexes and database-level immutability/state-machine guards.

CREATE INDEX idx_jobs_project_state_priority
    ON jobs(project_id, state, priority DESC, created_at);
CREATE INDEX idx_jobs_updated_at ON jobs(updated_at);
CREATE INDEX idx_job_dependencies_parent ON job_dependencies(depends_on_job_id);
CREATE INDEX idx_artifacts_project_hash ON artifacts(project_id, sha256);
CREATE INDEX idx_artifacts_project_status ON artifacts(project_id, status);
CREATE INDEX idx_artifact_dependencies_source ON artifact_dependencies(source_artifact_id);
CREATE INDEX idx_audit_events_project_time ON audit_events(project_id, occurred_at, id);
CREATE INDEX idx_audit_events_correlation ON audit_events(correlation_id)
    WHERE correlation_id IS NOT NULL;

CREATE TRIGGER audit_events_no_update
BEFORE UPDATE ON audit_events
BEGIN
    SELECT RAISE(ABORT, 'audit events are append-only');
END;

CREATE TRIGGER audit_events_no_delete
BEFORE DELETE ON audit_events
BEGIN
    SELECT RAISE(ABORT, 'audit events are append-only');
END;

CREATE TRIGGER artifact_content_is_immutable
BEFORE UPDATE ON artifacts
WHEN OLD.id IS NOT NEW.id
  OR OLD.project_id IS NOT NEW.project_id
  OR OLD.sha256 IS NOT NEW.sha256
  OR OLD.byte_length IS NOT NEW.byte_length
  OR OLD.relative_path IS NOT NEW.relative_path
  OR OLD.logical_type IS NOT NEW.logical_type
  OR OLD.media_type IS NOT NEW.media_type
  OR OLD.metadata_json IS NOT NEW.metadata_json
  OR OLD.engine_id IS NOT NEW.engine_id
  OR OLD.engine_version IS NOT NEW.engine_version
  OR OLD.model_id IS NOT NEW.model_id
  OR OLD.model_version IS NOT NEW.model_version
  OR OLD.model_weight_sha256 IS NOT NEW.model_weight_sha256
  OR OLD.parameters_json IS NOT NEW.parameters_json
  OR OLD.prompt_version IS NOT NEW.prompt_version
  OR OLD.provider_id IS NOT NEW.provider_id
  OR OLD.hardware_json IS NOT NEW.hardware_json
  OR OLD.quality_metrics_json IS NOT NEW.quality_metrics_json
  OR OLD.seed IS NOT NEW.seed
  OR OLD.reproducibility_level IS NOT NEW.reproducibility_level
  OR OLD.created_by IS NOT NEW.created_by
  OR OLD.created_at IS NOT NEW.created_at
BEGIN
    SELECT RAISE(ABORT, 'artifact content and provenance are immutable');
END;

CREATE TRIGGER jobs_validate_state_transition
BEFORE UPDATE OF state ON jobs
WHEN OLD.state <> NEW.state AND NOT (
       (OLD.state = 'QUEUED' AND NEW.state IN ('BLOCKED', 'PREPARING', 'CANCELLING', 'CANCELLED', 'STALE'))
    OR (OLD.state = 'BLOCKED' AND NEW.state IN ('QUEUED', 'CANCELLING', 'CANCELLED', 'STALE'))
    OR (OLD.state = 'PREPARING' AND NEW.state IN ('RUNNING', 'CANCELLING', 'FAILED', 'STALE'))
    OR (OLD.state = 'RUNNING' AND NEW.state IN ('PAUSING', 'CANCELLING', 'FAILED', 'SUCCEEDED', 'STALE'))
    OR (OLD.state = 'PAUSING' AND NEW.state IN ('PAUSED', 'CANCELLING', 'FAILED', 'STALE'))
    OR (OLD.state = 'PAUSED' AND NEW.state IN ('QUEUED', 'PREPARING', 'CANCELLING', 'CANCELLED', 'STALE'))
    OR (OLD.state = 'CANCELLING' AND NEW.state IN ('CANCELLED', 'FAILED'))
    OR (OLD.state = 'CANCELLED' AND NEW.state IN ('QUEUED', 'STALE'))
    OR (OLD.state = 'FAILED' AND NEW.state IN ('QUEUED', 'STALE'))
    OR (OLD.state = 'SUCCEEDED' AND NEW.state = 'STALE')
    OR (OLD.state = 'STALE' AND NEW.state = 'QUEUED')
)
BEGIN
    SELECT RAISE(ABORT, 'invalid job state transition');
END;

CREATE TRIGGER job_dependencies_same_project
BEFORE INSERT ON job_dependencies
WHEN (SELECT project_id FROM jobs WHERE id = NEW.job_id)
     IS NOT
     (SELECT project_id FROM jobs WHERE id = NEW.depends_on_job_id)
BEGIN
    SELECT RAISE(ABORT, 'job dependencies cannot cross projects');
END;

CREATE TRIGGER artifact_dependencies_same_project
BEFORE INSERT ON artifact_dependencies
WHEN (SELECT project_id FROM artifacts WHERE id = NEW.artifact_id)
     IS NOT
     (SELECT project_id FROM artifacts WHERE id = NEW.source_artifact_id)
BEGIN
    SELECT RAISE(ABORT, 'artifact dependencies cannot cross projects');
END;
