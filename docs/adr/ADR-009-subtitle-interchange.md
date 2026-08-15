# ADR-009: Exact, bounded subtitle interchange

Status: accepted for Phase 2 foundation  
Date: 2026-08-14

## Decision

SRT and WebVTT import use UTF-8 only and convert timestamps directly into integer ticks at an
exact 1,000-ticks-per-second rate. Floating-point seconds never enter the edit model. Parsing is
bounded by input bytes, cue count, cue text, and per-cue field lengths. Invalid, out-of-order, empty,
or negative-duration cues fail explicitly. Overlap remains legal because professional captions can
intentionally overlap.

Exports are deterministic. Publication stages and fsyncs a file, then creates the final name with
an atomic no-clobber hard link. Existing user files are never overwritten by the default API.
WebVTT cue settings are retained; STYLE and REGION blocks are rejected until the renderer can
represent them without loss.

## Consequences

- Bangla, Hindi, and all other Unicode text round-trip without a locale codec fallback.
- Millisecond subtitle exchange is exact and can be explicitly rescaled into project clocks.
- Unsupported styling fails visibly instead of being silently discarded.
- TTML/IMSC, ASS styling, SCC, and format-preserving metadata remain future adapters behind the
  same bounded document boundary.
