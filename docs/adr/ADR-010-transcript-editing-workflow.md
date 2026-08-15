# ADR-010: Revision-safe transcript editing workflow

- Status: Accepted
- Date: 2026-08-14

## Context

Transcript text and timing are shared inputs to translation, voice generation,
subtitles, and final renders. Automated recognition must not silently overwrite
human corrections, and concurrent editors must not lose changes.

## Decision

1. Transcript mutations are typed commands applied to an immutable revision
   snapshot; stale revisions fail with an explicit conflict.
2. Human edits, speaker/character assignment, approval, split, and merge are
   auditable operations. Locked fields reject automated ASR updates.
3. Split and merge preserve half-open rational time ranges and enforce ordering,
   non-overlap, and stable identifiers.
4. Every mutation returns invalidation roots for downstream translation, timing,
   subtitles, voice, and render artifacts. Consumers must invalidate by these
   roots rather than by ad-hoc filename conventions.
5. Transcript state is provider-neutral. ASR provenance remains attached to
   recognized segments and is never treated as human approval.

## Consequences

The workflow is deterministic and recoverable, while downstream jobs can rerun
only affected utterances. A future collaboration service can reuse the same
commands and revision checks over authenticated IPC without changing domain
semantics.
