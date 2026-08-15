# Benchmark fixture registry

This directory is a registry location, not a media drop folder. No benchmark audio, video,
transcript, speaker identity, face image, voice reference, or participant data is included in the
repository at this stage.

## Admission rule

A fixture may enter a benchmark run only after its immutable manifest and evidence record have been
approved. Possession of a file does not establish a right to benchmark it. The approval must cover
the specific processing purpose, languages, target territories, retention period, external-provider
disclosure (if any), and whether biometric/voice processing is permitted.

Each fixture set must have a unique directory outside the source tree and a manifest containing:

| Field | Required evidence |
| --- | --- |
| Dataset ID and version | Stable internal identifier; version never reused for changed bytes |
| Manifest SHA-256 | Lowercase digest of a canonical file manifest |
| File inventory | Project-relative path, byte length, media type, and SHA-256 for every file |
| Languages | Explicit `en`, `bn-BD`, and/or `hi-IN`; code-switch segments identified separately |
| Content license | Executed license or ownership record, permitted purpose, commercial-use decision |
| Participant consent | Consent/performer release or documented determination that it is not required |
| Voice/biometric scope | Whether ASR, diarization, speaker embeddings, cloning, and MOS review are allowed |
| Territories | Countries/regions in which collection, processing, review, and distribution are allowed |
| Privacy class | Public, confidential, restricted voice/biometric, or other approved class |
| Retention/deletion | Expiry, revocation contact, and deletion procedure |
| Provider disclosure | Approved provider IDs and data classes, or `none` for offline-only fixtures |
| Approvals | Dataset owner, legal/privacy reviewer, security reviewer, dates, and evidence references |

## Storage and access

- Store licensed media in the approved encrypted benchmark store, never Git or a developer cache.
- Use opaque fixture IDs in reports. Do not put participant names or source filenames in result JSON.
- Give runners read-only access. Generated output goes to a per-run staging directory.
- Verify every file hash before a run and fail closed on a missing, extra, or changed file.
- Keep provider-bound fixture subsets physically/logically distinct from offline-only data.
- Remove access promptly on consent revocation, license expiry, employment change, or project closure.
- A derived clip retains the restrictions of every source from which it was made.

## Minimum coverage design

The eventual legally approved golden set should cover clean and noisy dialogue, overlap, whispers,
shouting, music-heavy speech, code-switching, names and controlled terms, off-screen speech, multiple
speakers, varied ages/genders/accents, long and short timing slots, close-ups, and failure cases. Each
language cohort needs enough independent material to prevent tuning to a handful of clips.

Coverage goals do not authorize collection. Dataset owners must document sampling limitations and
known representation gaps so benchmark scores are not presented as universal accuracy.

## Current state

No fixture manifest is approved or shipped here. Consequently, there are no valid product model
benchmark results yet. Synthetic values used by unit tests under `tests/unit/benchmarks/` test schema
behavior only and are not quality evidence.
