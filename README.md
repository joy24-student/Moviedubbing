# AI Dubbing Studio

AI Dubbing Studio is a Windows-first, local-first workstation for professional multilingual
movie dubbing. The product combines a frame- and sample-accurate editorial timeline with an
artifact-based AI pipeline for transcription, translation, voice generation, timing, mixing,
subtitles, quality control, and selective visual dubbing.

This repository is at the platform-foundation stage. Its current contract is intentionally
small: the domain package defines durable media-time primitives and strict, versionable business
schemas. Desktop, persistence, worker, and media-engine layers consume these contracts without
being imported by them.

## Engineering principles

- Original media is immutable. Editing and generation produce new decisions and artifacts.
- Video edit time is rational; audio placement is represented as integer samples.
- Heavy media and AI work runs in supervised worker processes, never on the UI thread.
- Generated outputs are content-addressed and carry complete provenance.
- Voice consent and source authorization are domain data, not check-box-only UI state.
- Every long-running operation is idempotent, cancellable, resumable, and observable.
- Offline mode must produce no external network traffic.

## Prerequisites

- Python 3.12 x64
- Windows 10 or 11 for the supported desktop target
- Git and a current PowerShell

FFmpeg, GPU runtimes, and model packs are separately pinned and verified components; they are not
implicitly downloaded when the Python package is installed.

## Local setup

```powershell
py -3.12 -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
pytest
ruff check .
mypy src tests
```

The headless operator interface is available immediately after installation:

```powershell
aidub doctor --json
aidub project create "D:\Projects\Feature" --name "Feature" `
  --source-language en-US --operator producer --rights-basis "Licensed production"
aidub project validate "D:\Projects\Feature.aidub" --json
aidub media probe "D:\Media\feature.mkv" --json
```

Install `.[desktop]` to launch the Qt shell with `aidub-studio`, and provide a verified FFmpeg /
ffprobe runtime before media processing. `aidub doctor --require-runtime` is the machine-readable
readiness gate. Project creation always records the operator's source-rights assertion and never
overwrites an existing target.

Optional dependency groups are available for `desktop` and `persistence` development. Install only
the groups required by the component you are working on so that AI and media workers can retain
separate, locked runtime environments.

## Package boundaries

```text
src/aidub/domain/       pure business types and invariants
src/aidub/application/  use cases, commands, queries, orchestration policies
src/aidub/contracts/    versioned process and adapter messages
src/aidub/infrastructure/ persistence, filesystem, FFmpeg, credentials, telemetry
src/aidub/ui/           PySide6/Qt presentation
workers/                isolated media and AI worker entry points
```

Dependencies point inward. In particular, `aidub.domain` has no Qt, database, FFmpeg, provider, or
model imports.

## Domain conventions

All domain models use Pydantic v2 in strict, frozen mode and reject unknown fields. Identifiers have
stable prefixes (`prj_`, `med_`, `utt_`, `art_`, `job_`, and so on). Timestamps must be timezone
aware and are normalized to UTC. Ranges are half-open: `[start, end)`. Hashes are lowercase SHA-256
hex strings. Artifact paths are project-relative POSIX paths and may not traverse directories.

The canonical video representation is `RationalTime(ticks, rate)`, where `rate` is exact units per
second. A 23.976 fps frame uses the rate `24000/1001`; no floating-point seconds enter edit state.
The canonical audio representation is an integer sample position at the project working rate.
Conversions that can lose precision require an explicit rounding policy.

See [ADR-001](docs/adr/ADR-001-time-model.md) for the time-model decision and
`ENTERPRISE_IMPLEMENTATION_PLAN.md` for the phased delivery baseline.

## Implemented foundation

- Atomic create/open/validate/recover for active `.aidub` project directories.
- SQLite migrations, integrity checks, immutable artifacts, reconciliation, and audit events.
- Exact rational video time, integer audio samples, and strict versioned domain contracts.
- Spawned worker crash/cancellation isolation and canonical persisted job lifecycle.
- Bounded FFprobe import metadata, source hashes, privacy policy, DPAPI credentials, and JSON logs.
- English, Bangla (`bn-BD`), and Hindi (`hi-IN`) desktop catalogs and a dock-ready Qt shell.
- Headless project, diagnostics, media-probe, proxy, thumbnail, and waveform commands suitable
  for clean-machine CI.
- Deterministic subtitle interchange, revision-safe transcript editing, and a local ASR boundary
  with exact sample-clock chunking and auditable overlap merge warnings.

## Status

The project is pre-alpha. Phase 0 and Phase 1 are implemented, and Phase 2 now includes media
derivative generation plus transcript and speech pipeline boundaries; it is not yet a
CapCut/Premiere replacement. Real ASR/diarization models, translation, voice generation, timeline
playback/editing, mixing, QC, final render, and enterprise collaboration remain scheduled work in
`ENTERPRISE_IMPLEMENTATION_PLAN.md`. Do not entrust production masters or represent AI/provider
quality claims until the documented benchmark, licensing, clean-Windows, security, and release
gates pass.
# Moviedubbing  
