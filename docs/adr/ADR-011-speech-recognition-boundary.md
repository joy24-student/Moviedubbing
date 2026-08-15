# ADR-011: Local speech-recognition boundary and deterministic long-form merge

- Status: Accepted
- Date: 2026-08-14

## Context

Feature-length media is too large to recognize as one model invocation. Different
ASR runtimes also expose incompatible timestamp units, model naming, cancellation,
and progress APIs. Floating-point seconds and implicit model upgrades would make a
transcript impossible to reproduce exactly, while naive overlapping chunks create
duplicate words at every seam.

The studio must support English, Bengali, Hindi, and other BCP 47 languages without
sending audio to a network service by default. This phase defines the boundary only;
it does not download or execute a particular model.

## Decision

1. All ASR requests and outputs use half-open integer `AudioSampleRange` values in
   the decoded source stream's sample clock. Floating-point seconds are forbidden at
   this boundary.
2. Each result records engine version, model version, exact model-weight SHA-256,
   source-audio SHA-256, project/media IDs, language, channel, full range, and chunk
   range. Words and segments carry that provenance and immutable confidence values.
3. `SpeechRecognizer` is a synchronous local-engine protocol. Worker/process policy
   remains outside the recognizer adapter. A small runtime protocol supplies
   cooperative cancellation checkpoints and validated progress events.
4. Long inputs are balanced across the minimum number of chunks that satisfy a hard
   maximum. Adjacent chunks use the configured integer-sample overlap exactly. If
   maximum, minimum, and overlap constraints cannot all be met, planning fails.
5. Merge compatibility is fail-closed. Results with a different request, project,
   media asset, source hash, language, audio channel, sample clock, chunk plan, or
   model build are rejected rather than guessed or rescaled.
6. Overlapping tokens are resolved deterministically: higher confidence wins; ties
   prefer the lower chunk index, then earlier timing and stable ID. Unicode text is
   compared after NFC normalization and case folding only for duplicate detection;
   emitted text is never rewritten.
7. A conflicting token may be dropped to keep the merged sequence monotonic, but a
   timestamp is never shifted. Every dropped overlap emits an auditable warning that
   identifies both retained and removed words.

## Consequences

- Hour-scale arithmetic is exact and replayable on every supported machine.
- Model adapters remain replaceable and testable with injected fakes.
- The persistence layer can invalidate transcripts when either source bytes or model
  weights change.
- Seam conflict warnings become explicit QC inputs instead of hidden timing edits.
- Recognition adapters must convert their native timestamps into exact sample ranges
  and provide model-weight hashes before their output is accepted.

## Rejected alternatives

- Floating-point seconds: cumulative rounding and platform-dependent ordering.
- Provider-specific result objects in the domain: locks project data to one SDK.
- Concatenating chunk text: duplicates seams and loses word-level timing.
- Silently moving overlapping words: corrupts model evidence and hides QC defects.
- Automatic model downloads in the core: violates local-first, reproducibility, and
  controlled-deployment requirements.
