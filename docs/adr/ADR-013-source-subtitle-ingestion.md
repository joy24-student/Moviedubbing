# ADR-013: Source subtitle ingestion as deterministic transcript candidates

- Status: Accepted
- Date: 2026-08-14

## Context

Existing SRT and WebVTT files can be valuable alignment hints or translation inputs, but a
caption file is untrusted input and is not proof that its text, timing, language, or speaker
attribution is correct. A project must retain enough evidence to reproduce an import while
avoiding machine-specific paths, implicit text encoding fallback, floating-point timestamps, and
partial transcript updates.

## Decision

1. Source subtitle ingestion accepts only regular local UTF-8 or UTF-8-with-BOM SRT/WebVTT files.
   It is bounded by bytes, cue count, and Unicode character count, never writes the source, and
   rejects links/reparse points at the import boundary.
2. The source language is mandatory BCP 47 input. It is never guessed from a filename, operating
   system locale, or subtitle stream tag. Imported text remains Unicode text exactly as parsed;
   no transliteration, translation, speaker inference, or approval is implied.
3. Every successful parse produces a provenance record with display name, format, encoding,
   byte length, and SHA-256 of the exact input bytes. Absolute source paths are deliberately not
   included in project-facing provenance.
4. Each cue becomes a deterministic draft `Utterance` candidate scoped by project, media asset,
   source-byte hash, and cue ordinal. Candidate confidence is `0.0` because captions contain no
   ASR confidence measurement and candidate status is never upgraded automatically.
5. Source timing stays at the exact 1 kHz subtitle clock. Mapping to another edit clock requires
   exact representability or a caller-selected rounding policy. The service reports overlapping
   source cues as warnings and reports out-of-media, nonrepresentable, or collapsed edit ranges as
   blocking conflicts.
6. Candidate emission is all-or-nothing. A successful parse with blocking conflicts still returns
   a typed report, but emits no candidates until the caller resolves or explicitly changes the
   timing policy. Consumers may call `require_acceptable` to make that fail-closed gate explicit.

## Consequences

- Subtitle-assisted alignment is reproducible, auditable, and safe for Bengali, Hindi, English,
  and other Unicode languages without a locale-dependent codec fallback.
- Existing professional caption overlap is preserved for review rather than silently merged or
  shifted.
- Later persistence, UI, and transcript-revision services can record the report and commit an
  accepted candidate set without coupling this boundary to SQLite, Qt, FFmpeg, or a network API.
- ASS/SSA, TTML/IMSC, embedded-container extraction, caption QC, and user conflict resolution
  remain future adapters/workflows behind this immutable boundary.
