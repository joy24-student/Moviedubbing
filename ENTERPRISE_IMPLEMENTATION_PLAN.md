# AI Movie Dubbing Studio - Enterprise Implementation Plan

Status: actively implemented baseline (Phase 0 complete; Phase 1 complete; Phase 2 in progress)  
Prepared: 2026-08-14  
Target: production-grade Windows desktop application  
Source documents:

- AI_Movie_Dubbing_Studio_Python_Project_Documentation.pdf, 59 pages, version 1.0
- AI_Movie_Dubbing_Studio_Master_Specification_v2-1.md, 1,726 lines, sections 1-78

## 1. Executive decision

Build a dubbing-first professional non-linear editor (NLE), not a generic video editor that happens to include dubbing.

The first production product must equal professional editing software in reliability, responsiveness, timeline precision, keyboard workflow, recoverability, and export correctness. It should not claim complete CapCut or Premiere Pro feature parity in its first release. Full general-purpose NLE parity is a separate multi-year program.

The recommended product sequence is:

1. Professional AI dubbing workstation with a frame- and sample-accurate editorial timeline.
2. Creator editing expansion: captions, graphics, transforms, transitions, keyframes, templates, and basic color.
3. Studio expansion: multi-user review, remote workers, shared storage, RBAC, SSO, policy control, and broadcast deliverables.
4. General NLE expansion: nested sequences, multicam, advanced effects/color, plugin SDK, and deeper interchange.

Python remains the application and orchestration language. Performance-critical work must use native, GPU-accelerated runtimes through stable adapters. "Python-only" must not mean reimplementing codecs, rendering, audio DSP, graphics, or CUDA inference in pure Python.

## 2. Audit result and current baseline

### 2.1 Repository state

The implementation has moved beyond the greenfield audit. The current repository
contains a typed Python package, strict domain/time contracts, project-package
storage, WAL SQLite migrations, content-addressed artifacts, locking and catalog
services, a headless CLI, diagnostics, an optional PySide6 shell, i18n catalogs,
subtitle interchange, deterministic media derivatives, transcript editing
commands, and a local speech-recognition boundary. CI, packaging smoke tests,
benchmarks, ADRs, and traceability documents are present.

Verified baseline on 2026-08-14: 512 tests passed and 3 were skipped because
optional PySide6 or host symlink permissions were unavailable; Ruff, formatting,
and strict mypy pass. This is a production-oriented foundation, not a finished
CapCut/Premiere replacement. Native playback, real model adapters, GPU workers,
timeline rendering, translation/TTS, QC, export certification, signed release
packaging, and enterprise collaboration remain planned work.

### 2.2 Documentation quality

The specification is a strong product vision and correctly emphasizes local-first processing, immutable artifacts, isolated workers, provider adapters, partial rerendering, consent, and crash recovery.

Before it can drive engineering, the following issues must be resolved:

- The filename says v2-1, the title says v2.0, and the document-control table still says v1.0.
- The Markdown contains mojibake and broken diagrams.
- P0 scope is too large for one release and mixes MVP, professional editing, visual dubbing, packaging, and enterprise operations.
- Most non-functional requirements are qualitative rather than measurable.
- Time is represented in milliseconds; a professional editor needs rational frame time and integer audio-sample positions.
- The playback, preview-compositing, media-conform, color-management, and interactive-audio engines are under-specified.
- "Unofficial" provider endpoints are unsuitable for a production product.
- The model list is illustrative but not release-safe. Models, weights, training data, transitive dependencies, and commercial rights need separate approval.
- General NLE functions implied by the CapCut/Premiere comparison are mostly outside the current requirements.
- Enterprise identity, policy, shared-workflow, supply-chain security, fleet deployment, support, and service objectives need explicit designs.

### 2.3 Product boundary

Release 1 is successful when a professional can import a two-hour film, analyze it once, create and edit multiple dubbed languages, recover from failures, rerender only affected segments, and export verified deliverables.

Release 1 does not need advanced color grading, motion graphics, arbitrary third-party effects, multicam editing, or every camera codec. It must provide reliable interchange so those tasks can continue in Premiere Pro, Resolve, or another NLE.

## 3. Target capability map

| Capability tier | Included |
| --- | --- |
| Dubbing core, P0 | Media import/proxy, ASR, diarization, characters, translation, glossary, consent-aware voice, timing, M&E/stems, subtitles, QC, render/export |
| Professional editor, P0 | Rational time model, source/dub viewer, precise seek, utterance and audio tracks, trim/split/merge, snapping, markers, J/K/L, undo/redo, versions, partial rerender |
| Visual dubbing, P1 | Shot/face analysis, active-speaker confidence, selective preview/final lip-sync, original-shot fallback |
| Creator NLE, P2 | Transitions, text/graphics, transforms, speed, basic effects/color, keyframes, templates, masks, tracking |
| Studio enterprise, P2 | Shared projects, remote workers, review/approval, RBAC/SSO, admin policy, fleet updates, usage controls |
| Full NLE program, P3 | Nested sequences, multicam, advanced color/effects, deep plugin ecosystem, broad format/camera certification |

## 4. Non-negotiable architecture

### 4.1 Runtime topology

~~~text
Signed Windows Desktop Application
|
+-- UI process
|   +-- PySide6 application shell
|   +-- Qt Quick accelerated timeline/viewer surfaces
|   +-- docked inspectors, editors, command palette
|   +-- local IPC client
|
+-- Project and orchestration process
|   +-- single project-state writer
|   +-- job DAG and checkpoints
|   +-- artifact/catalog service
|   +-- cache invalidation
|   +-- policy, rights, provider router
|
+-- Media worker pool
|   +-- FFprobe/FFmpeg
|   +-- proxy, thumbnail, waveform
|   +-- decode/conform, mix, mux, encode
|
+-- CPU worker pool
|   +-- text normalization and subtitles
|   +-- provider calls and schema validation
|   +-- QC aggregation
|
+-- GPU worker supervisor
    +-- ASR/forced alignment
    +-- diarization/embeddings
    +-- TTS/voice conversion
    +-- source separation
    +-- vision/lip-sync
~~~

Heavy work never runs in the UI process. A worker crash, CUDA out-of-memory error, malformed media file, or provider failure must not terminate the editor.

### 4.2 Architectural layers

- Domain: projects, timelines, media, characters, utterances, rights, artifacts, jobs, QC, and exports. It contains no Qt, FFmpeg, database, provider, or model-specific code.
- Application: use cases, commands, queries, transactions, invalidation rules, and orchestration.
- Contracts: versioned Pydantic and Protobuf schemas for IPC, jobs, artifacts, events, and adapters.
- Infrastructure: SQLite, filesystem, credential storage, FFmpeg, logging, telemetry, IPC, updater.
- Adapters: one package per ASR, diarization, LLM, TTS, separation, vision, lip-sync, and interchange implementation.
- Presentation: PySide6/Qt Quick screens, view models, keyboard command system, accessibility.

Dependencies point inward. Engine packages may implement contracts; the domain never imports an engine package.

### 4.3 IPC and state ownership

- Use versioned Protobuf messages over authenticated local IPC. A later remote transport must reuse the same logical contracts.
- The orchestration process is the only project-database writer.
- UI state is a view of persisted project state plus temporary selection/playback state.
- Workers receive immutable job descriptors and input artifact references. They return progress events and a staged artifact manifest.
- A worker must never mutate project tables or publish directly into the final artifact namespace.
- Every process provides a version handshake, capability list, heartbeat, health state, and graceful-cancel protocol.
- Terminal job success is emitted only after artifact verification and the project transaction commit.

### 4.4 Process and dependency isolation

The desktop shell, media workers, and major AI engines should be separately packageable. Each AI worker may have its own locked dependency environment because CUDA, PyTorch, CTranslate2, ONNX, and model packages frequently conflict.

The application installer remains small. Model/engine packs are separately signed, hashed, versioned, installable, removable, and pin-able per project.

## 5. Recommended technology baseline

Final versions are selected and pinned after Phase 0 compatibility tests.

| Area | Baseline |
| --- | --- |
| Language | Python 3.12 x64 control plane; per-worker compatibility runtimes where justified |
| Desktop | PySide6; Qt Widgets for shell/docks and Qt Quick Scene Graph for hot timeline/viewer surfaces |
| Media | Signed/pinned FFmpeg and FFprobe build; PyAV only where direct frame access is proven useful |
| Timeline interchange | OpenTimelineIO plus product-specific schemas |
| Validation | Pydantic v2 and JSON Schema |
| Database | SQLAlchemy 2, SQLite WAL, Alembic migrations |
| IPC | Protobuf contracts over Windows named pipe or authenticated local transport |
| Async | asyncio/qasync for UI-side coordination; spawned processes for compute |
| Numeric/audio | NumPy, soundfile, soxr-class resampling, native DSP/FFmpeg filters |
| AI | PyTorch/CUDA, CTranslate2, ONNX Runtime or TensorRT only after benchmark evidence |
| Logs/traces | structlog JSON plus OpenTelemetry-compatible internal spans |
| Tests | pytest, pytest-qt, Hypothesis, golden media fixtures, GPU benchmark harness |
| Packaging | PyInstaller or Nuitka spike; signed MSI/MSIX/bootstrapper; models outside core app |
| Tooling | pyproject.toml, locked dependencies, Ruff, strict type checking, pre-commit |

Qt Quick is selected for the high-density timeline because its retained scene graph can batch rendering and use a dedicated render thread. Traditional widgets remain appropriate for forms and docking.

### 5.1 Playback strategy

Playback is a separate engine, not a QMediaPlayer convenience feature.

Phase 0 must compare:

1. An embedded libmpv-based proxy player for rapid delivery.
2. A custom FFmpeg/PyAV frame server with audio-clock master, decode queues, and GPU texture upload.
3. A hybrid where libmpv handles source playback while a render graph produces edited previews.

The selected engine must demonstrate:

- frame-accurate seek on constant-frame-rate media
- deterministic variable-frame-rate conform
- source/dub A/B and split comparison
- audio scrub and J/K/L shuttle
- waveform/playhead synchronization
- proxy/original time mapping
- no UI-thread decode
- correct rotation, pixel aspect ratio, color metadata, and HDR warning/fallback

### 5.2 Media conform and color

- Record codec profile/level, time base, frame rate mode, field order, rotation, sample/display aspect ratio, pixel format, range, primaries, transfer, matrix, mastering metadata, and content-light metadata.
- Make project working color space and preview-display transform explicit.
- Preserve source color/HDR metadata on remux paths and validate it after export.
- Use a benchmarked tone-map only for an SDR preview of HDR content; never bake it into the master without an explicit export decision.
- Treat interlaced, variable-frame-rate, unsupported HDR, and unusual channel layouts as conform cases with visible warnings.
- Define proxy recipes by source class and verify proxy/original frame mapping.
- Maintain separate LGPL/GPL FFmpeg build decisions and a codec/license manifest for every distributed media runtime.

### 5.3 Time model

Do not use float seconds or millisecond integers as the canonical edit representation.

- Video time uses rational values: integer ticks plus rate.
- Audio placement uses integer sample positions at the project working rate.
- Source PTS/DTS, edit time, source time, and generated-artifact time are distinct fields.
- Drop-frame/non-drop-frame display is presentation logic.
- Variable-frame-rate media gets an explicit conform map.
- Database constraints reject negative or inverted ranges.
- All edit, cache, subtitle, mix, and render math shares one tested time library.

OpenTimelineIO is used for interchange and concepts, not as the sole project database.

## 6. Project, data, and artifact design

### 6.1 Project package

An active project is a directory, not a monolithic zip:

~~~text
ProjectName.aidub/
  manifest.json
  project.db
  source-links/
  proxy/
  thumbnails/
  waveforms/
  artifacts/sha256/aa/...
  localizations/bn-BD/
  localizations/hi-IN/
  renders/
  recovery/
  logs/
~~~

Collect/archive creates a verified portable package; editing does not continually rewrite one huge archive.

### 6.2 Core schemas

Add the specification's dubbing entities plus:

- Sequence, Track, Clip, Gap, Transition
- RationalTime, TimeRange, ConformMap
- EditCommand, UndoGroup, Marker, Approval
- EffectInstance, Parameter, Keyframe
- AudioBus, AutomationPoint, ChannelMap, LoudnessMeasurement
- PromptTemplate, PromptVersion, TranslationMemoryEntry
- ModelPackage, EnginePackage, CompatibilityRecord, BenchmarkRun
- ProviderPolicy, ProviderRequestAudit, DataDisclosure
- ProjectLock, RecoverySnapshot, SchemaMigration
- ExportPreset, Deliverable, ValidationResult
- UserIdentity, Role, ReviewTask for future studio mode

### 6.3 Database rules

- Enable foreign keys, WAL, busy timeout, integrity checks, and explicit migrations.
- Use one writer and short transactions; never keep a transaction open during inference or FFmpeg.
- Store large binary data in the artifact store, not SQLite.
- Publish artifacts with stage -> flush -> hash -> atomic rename -> database commit.
- On startup, reconcile abandoned staged files and incomplete jobs.
- Keep an application catalog database separate from project databases.
- Open newer unsupported schemas read-only; never guess a downgrade.
- Back up before migration and test forward migration from every supported release.

### 6.4 Immutability, caching, and invalidation

Each artifact records:

- content hash and byte length
- logical type and media metadata
- source artifact hashes
- engine package, model, weight hash, and code version
- normalized settings and seed
- prompt/provider versions when applicable
- hardware and precision
- quality measurements
- exact, best-effort, or non-reproducible classification

Cache keys are derived from canonical serialized inputs, engine ABI, model/weight hashes, parameters, prompt version, and dependency hashes.

Invalidation is graph-based. Editing one translation invalidates that language's downstream voice, timing, optional lip-sync, mix, QC, and export nodes only. Approved human translations are marked stale when a glossary changes; they are never silently destroyed.

Garbage collection is reachability-based with a recoverable trash window and a dry-run size report.

## 7. Job orchestration and GPU scheduling

### 7.1 Job contract

Every job has:

- stable ID and idempotency key
- project, localization, scene/shot/utterance scope
- typed input and expected output contracts
- resource request: CPU, RAM, VRAM, scratch disk, provider quota
- priority, dependencies, retry policy, and deadline
- progress units and checkpoint interval
- cancellation-safe boundaries
- error category and remediation hint
- artifact publication transaction

States are QUEUED, BLOCKED, PREPARING, RUNNING, PAUSING, PAUSED, CANCELLING, CANCELLED, FAILED, SUCCEEDED, and STALE.

### 7.2 Scheduler policy

- Use resource reservations rather than starting work and hoping memory is available.
- Maintain observed VRAM profiles by engine/model/hardware, not only vendor estimates.
- Prefer a warm model when it avoids a costly load and does not starve a higher-priority job.
- Batch compatible utterances within bounded latency.
- Apply backpressure when artifact write throughput or provider quota is saturated.
- Use weighted fair scheduling across projects/languages.
- In Cinema mode, never silently change model, precision, or quality.
- A downgrade is a new visible job decision with provenance.

### 7.3 OOM recovery

1. Record requested, reserved, free, and peak VRAM.
2. Cleanly terminate/restart only the failed worker if CUDA state is unsafe.
3. Retry once with a validated smaller batch/chunk.
4. Unload lower-priority warm models and retry.
5. Route to another compatible GPU or queue.
6. Offer a policy-approved model/precision change; require confirmation in Cinema mode.

### 7.4 Crash recovery

- Checkpoint at utterance/shot boundaries or at least every 10 seconds of long work.
- Worker heartbeats are supervised.
- Stale leases return to queued state after process death.
- Partially written outputs stay staged and are never visible as complete artifacts.
- Closing the UI may leave an explicitly approved background render running.
- A forced process kill must not corrupt source media, the database, or completed artifacts.

## 8. End-to-end product pipeline

### 8.1 Shared source analysis

1. Verify rights acknowledgment and source readability.
2. FFprobe all streams, chapters, attachments, subtitles, color/HDR metadata, time bases, and channel layouts.
3. Hash source identity using a fast fingerprint first and full hash in background.
4. Detect variable frame rate and build conform mapping.
5. Create edit proxy, thumbnails, waveform levels, and lossless reference audio.
6. Import subtitles as optional alignment hints.
7. Detect scenes/shots in parallel with audio analysis where safe.
8. Acquire M&E/stems or run the selected separation fallback.
9. Run VAD, ASR, word alignment, diarization, overlap detection, and confidence analysis.
10. Build speaker clusters, face tracks, active-speaker links, and editable character candidates.

### 8.2 Localization pipeline

1. Create target-language policy, glossary, pronunciation dictionary, and style guide.
2. Generate scene memory and character context.
3. Produce a semantic translation draft.
4. Run cultural/style adaptation.
5. Enforce terminology and named entities.
6. Estimate spoken duration and create shorter/longer alternatives.
7. Use an independent critic/provider when policy allows.
8. Route uncertain or material story changes to human review.
9. Create authorized voice takes with explicit engine/seed/settings provenance.
10. Forced-align the generated take and fit timing using rewrite, pauses, model controls, then bounded high-quality stretch.
11. Apply scene acoustic treatment and mix with M&E.
12. Generate subtitles and QC results.
13. Optionally render eligible lip-sync shots.
14. Run preflight, render, verify, and publish deliverables.

### 8.3 Human control

Every generated decision exposes:

- source and generated versions
- confidence and measurable reasons
- inputs, engine/model/provider, and settings
- lock/approve/reject/regenerate controls
- alternatives and A/B preview
- affected downstream artifacts before an edit is committed
- undo/redo and audit history

## 9. AI and provider production policy

### 9.1 Provider integrations

Production builds use official, authorized APIs only. Do not ship cookie scraping, session-token reuse, browser automation, or unofficial account endpoints.

The canonical provider adapter reports:

- supported tasks and modalities
- structured-output strength
- model/version identifiers
- context/output limits
- latency, price estimate, quota, and region
- data retention/training policy metadata supplied by configuration
- health, failure rate, and circuit state

OpenAI integrations should use the Responses API for new work and strict Structured Outputs for translation/QC objects. Gemini supports JSON Schema/Pydantic structured output. DeepSeek JSON mode guarantees valid JSON but may return empty content; all responses therefore receive local schema and semantic validation.

Provider responses are never authoritative. They are untrusted data:

- Parse with strict schemas and forbid unknown fields where appropriate.
- Validate target language, glossary, timing ranges, omissions, and prohibited transformations.
- Use bounded retries with jitter only for safe/idempotent requests.
- Circuit-break unhealthy providers.
- Keep manual editing available if every provider is offline.
- Store response hashes and redacted request metadata, not sensitive raw prompts by default.
- Pin model versions when available and re-run evals before changing defaults.

### 9.2 Local model registry

No model is enabled by popularity alone. Each engine/model package must include:

- code, model-weight, and dependency licenses
- permitted commercial use and attribution obligations
- model card and training-data disclosures when available
- signed manifest, URLs, SHA-256 hashes, and total disk size
- compatible app/engine/CUDA/driver versions
- supported languages and known limitations
- observed RAM/VRAM and speed by hardware tier
- quality benchmark results
- telemetry/network behavior and offline verification
- safety/provenance/watermark requirements

Current candidates are evaluation inputs, not commitments:

- faster-whisper is a credible ASR baseline with batching, quantization, VAD, and word timestamps.
- pyannote community models are a diarization baseline, but their user conditions, access-token setup, optional telemetry, and offline packaging need explicit handling.
- Chatterbox is a TTS candidate, subject to Bengali/Hindi quality and complete transitive-license review.
- F5-TTS pretrained weights must not ship in a commercial default because the official repository identifies them as CC-BY-NC.
- The original Meta Demucs repository is not actively maintained; source separation needs a maintained candidate bake-off or an internally supported fork.
- MuseTalk and LatentSync are lip-sync candidates only after model, dependency, test-data, and output-use review.

### 9.3 Benchmark program

Create a legally usable, versioned benchmark pack with:

- English, Bengali, and Hindi first; code-switching in both directions
- principal/secondary voices, accents, children/adults where licensed
- overlap, whispers, shouting, laughter, breaths, off-screen dialogue
- music-heavy, noisy, reverberant, phone, vehicle, and exterior scenes
- close-up, profile, occluded, facial hair, rapid cuts, and low-light shots
- names, honorifics, idioms, profanity policy, and domain terminology

Track:

- ASR WER/CER, named-entity recall, timestamp error
- diarization DER/JER and overlap/speaker-confusion error
- translation adequacy, fluency, terminology, style, and duration fit
- TTS intelligibility, pronunciation, speaker similarity, naturalness, hallucination/artifact rate
- timing delta, overlap, pauses, and stretch ratio
- lip-sync objective score plus blinded human close-up review
- separation leakage/artifacts and mix intelligibility
- stage and end-to-end real-time factor, cold/warm latency, RAM/VRAM, and failure rate

Defaults change only through a benchmarked model promotion process with rollback.

## 10. Professional editing experience

### 10.1 Release-1 workspace

- Home/recovery
- new project and media conform
- project bin and scene browser
- analysis center
- translation, glossary, and pronunciation studio
- character/voice/performance studio
- source/dub/compare viewer
- professional dubbing timeline
- audio mixer and subtitle editor
- QC heatmap and issue inspector
- jobs/render/export
- model/provider/GPU/storage/privacy/rights/settings/diagnostics

### 10.2 Timeline minimum

- video, lip overlay, source dialogue, dub dialogue, M&E, music, effects, ambience, and subtitle tracks
- select, blade, split/merge utterance, trim, ripple trim, roll, slip, slide
- snapping, linked selection, track targeting, lock, mute, solo
- markers, ranges, loop, zoom, horizontal/vertical navigation
- J/K/L shuttle, audio scrubbing, frame step, go-to timecode
- per-utterance status, confidence, approval, version, and QC badges
- multi-resolution cached waveforms and progressive thumbnails
- command-based undo/redo across every editorial mutation
- layout workspaces and user-remappable shortcuts
- scalable high-DPI UI, visible focus, text/icon status in addition to color

### 10.3 Interchange

Ship reliable OTIO export/import first, then validate EDL and FCPXML adapters. Treat AAF as a separately tested/licensed integration. Always support:

- source and target subtitle files
- consolidated dialogue/M&E/music/effects stems
- timecode and channel-layout reports
- cue sheets, pronunciation/glossary reports, and QC report
- a collected project manifest with hashes

This provides a professional Premiere/Resolve handoff before the product implements every general editing function.

### 10.4 General NLE expansion

After the dubbing editor is stable, add in this order:

1. transforms, crop, opacity, text/titles, keyframes
2. transitions, speed changes, freeze frames, simple compositing
3. captions/templates, masks, tracking, stabilization, basic color/LUT
4. nested sequences, adjustment layers, multicam
5. effect/plugin SDK and advanced color/audio features

Each addition must use the same render graph, time model, undo system, proxy map, and export validation rather than becoming a separate feature path.

## 11. Audio and render contract

- Use 48 kHz float working audio unless a project preset requires otherwise.
- Preserve original sample rate, bit depth, channel layout, and timecode metadata in provenance.
- Prefer supplied M&E; source separation is a visibly labeled fallback.
- Never normalize each utterance independently in a way that destroys scene dynamics.
- Maintain dialogue buses and scene/character automation.
- Every acoustic treatment is bypassable and A/B comparable.
- Use two-pass loudness analysis for file delivery where required.
- Loudness and true-peak targets belong to named export presets, not global constants.
- Preserve original video by remux when no visual frames changed.
- Re-encode only changed video ranges when the container/codec workflow can do so safely; otherwise make the full re-encode explicit.
- Validate duration, stream count, codecs, language tags, channel maps, subtitle timing, black/silent gaps, loudness, true peak, and output hashes before success.

## 12. Performance and quality objectives

Measure on three published reference systems:

- Entry: 8 GB VRAM, 32 GB RAM, modern 8-core CPU, NVMe
- Pro: 16 GB VRAM, 64 GB RAM, modern 12-core CPU, NVMe
- Studio: 24 GB or more VRAM, 128 GB RAM, optional second GPU, fast NVMe scratch

Initial SLOs for the Pro system:

| Area | Target |
| --- | --- |
| App shell cold start | p95 under 5 seconds, excluding model download/load |
| Open indexed two-hour project | p95 under 3 seconds to editable metadata view |
| Editor command response | p95 under 50 ms for local edit commands |
| Proxy timeline | sustained 60 fps UI at 1080p proxy with no inference on scroll/zoom |
| Seek | p95 under 250 ms on indexed proxy |
| Job pause/cancel acknowledgment | p95 under 500 ms; completion at next declared safe boundary |
| Autosave/checkpoint | visible within 2 seconds without blocking input |
| Crash reopen | under 30 seconds to recover project/job state |
| ASR baseline | real-time factor no worse than 0.20 after warmup, quality gate still met |
| Audio-dub draft | 60 minutes of source in 30 minutes or less after source analysis, excluding human/provider latency |
| Partial regeneration | one edited utterance schedules only its declared downstream dependency set |
| Data integrity | zero original-media mutation and zero accepted corrupt artifacts |

### 12.1 Provisional quality gates

Phase 0 replaces provisional thresholds with measured per-language baselines. Until then:

| Area | Gate |
| --- | --- |
| ASR | Every segment below the approved confidence/quality threshold is visibly flagged; no benchmark release regression beyond the agreed tolerance |
| Named entities/glossary | 100% of critical controlled terms are correct or blocking-review items |
| Translation | No critical meaning-change issue can pass release; independent human adequacy/fluency sampling is required |
| Timing | At least 95% of approved non-overlap lines are within +/-8% of their target slot; all exceptions are visible |
| Voice | Zero unflagged extra/hallucinated speech, clipping, wrong-character assignment, or missing authorization |
| Audio | Zero digital clips; integrated loudness and true peak meet the selected preset within its declared tolerance |
| Lip-sync | Every failed high-visibility shot is rejected or explicitly waived; original-shot fallback is always available |
| Export | No missing stream, invalid language tag, unexpected duration drift, corrupt packet, or failed player/NLE compatibility check |

### 12.2 Performance/quality presets

| Preset | Policy |
| --- | --- |
| Draft | Small/fast approved engines, proxy media, limited review, no final lip-sync; optimized for interactive iteration |
| Fast | High-quality ASR and voice with reduced review passes and limited visual work |
| Professional | Full context, character continuity, timing, stem mix, selective lip-sync, and required QC |
| Cinema | Highest approved engines, independent language review, strict QC/approval, final visual pass; no silent downgrade |
| Offline Private | Best locally installed approved engines; outbound network blocked and verified |

Model-dependent targets are provisional until Phase 0. Latency is never improved by silently lowering a required quality gate.

Performance engineering includes:

- proxy-first playback and decode-ahead
- visible-range-only timeline rendering
- multilevel waveform and thumbnail caches
- scene/utterance chunking
- warm model workers
- compatible micro-batching
- pinned memory and asynchronous transfers where measured useful
- NVDEC/NVENC or equivalent only behind capability checks
- remux/copy paths when possible
- bounded concurrency based on CPU, RAM, VRAM, disk, and thermal state
- performance traces and a 10% regression alert/gate

## 13. Security, privacy, rights, and provenance

### 13.1 Threat model

Treat media files, subtitle files, model packages, archives, provider responses, and project packages as untrusted inputs.

Required controls:

- restricted media/model worker permissions and per-job temp directories
- archive path-traversal and reparse-point defenses
- FFmpeg/model timeouts, memory/disk limits, and crash containment
- no arbitrary pickle loading from untrusted model packages; prefer safe weight formats
- signed/hash-verified app, engine, model, and update manifests
- TLS verification and an endpoint allowlist
- no provider/model network access in Offline mode
- secrets in Windows Credential Manager or DPAPI-backed storage, never project files
- sanitized logs/support bundles
- dependency scanning, SBOM, license inventory, and reproducible release manifests
- Windows code signing and signed update metadata with rollback protection

### 13.2 Rights controls

- Source-media authorization is acknowledged at project creation.
- Voice consent/license records include subject/owner, evidence reference, purpose, languages, territory, expiry, revocation, and approver.
- Revoked voice profiles cannot generate or enter a new final export.
- Exports record which external providers received which data categories.
- Audit events are append-only and hash-chained for professional/studio policy modes.
- Generated-media provenance can include C2PA Content Credentials where the output/container supports the selected implementation.
- Required third-party watermarks/provenance are preserved.

Legal counsel must approve the shipped license matrix, privacy disclosures, provider terms, consent workflow, and target-market compliance. Engineering documentation must not claim certification merely because controls are planned.

## 14. Reliability and observability

### 14.1 Error taxonomy

Use typed, user-actionable categories:

- invalid/unsupported media
- missing/relinked source
- storage full/read-only/corrupt
- database migration/integrity
- worker crash/timeout/cancel
- CUDA/driver/VRAM incompatibility
- model missing/hash/license/incompatible
- provider auth/rate/timeout/schema/content
- quality-gate failure
- export preflight/encode/validation
- rights/policy block

Each error has a stable code, safe user message, technical context, retryability, remediation, and correlation ID.

### 14.2 Observability

- structured local logs with project/job/stage/asset/utterance correlation
- spans for queue, model load, inference, artifact publish, and provider calls
- CPU/RAM/GPU/VRAM/disk/temperature samples at bounded frequency
- FFmpeg command manifest and sanitized stderr
- provider health, latency, retry, circuit, and usage estimates
- crash/minidump metadata with explicit opt-in for upload
- support bundle preview and redaction test
- local metrics by default; external telemetry is opt-in and policy-controlled

## 15. Engineering repository and quality gates

Recommended initial structure:

~~~text
apps/
  desktop/
  cli/
src/aidub/
  domain/
  application/
  contracts/
  infrastructure/
  adapters/
  orchestration/
  ui/
workers/
  media/
  asr/
  diarization/
  voice/
  separation/
  vision/
  lipsync/
migrations/
tests/
  unit/
  contract/
  integration/
  ui/
  recovery/
  security/
  packaging/
benchmarks/
fixtures/
packaging/
docs/
  adr/
  product/
  runbooks/
~~~

Every merge requires:

- formatting, lint, strict type checks
- unit and contract tests
- migration checks when schemas change
- security/secret/dependency/license scans
- code review by an owner of the affected subsystem
- performance/quality comparison when a hot path, prompt, provider, or model changes

Coverage percentage is not the only gate. Domain/time/cache/invalidation code requires exhaustive and property-based tests. Adapter code requires shared contract suites. Critical UI workflows require packaged-app tests.

## 16. Test architecture

### 16.1 Test layers

- Unit: rational time, ranges, cache keys, invalidation, text normalization, rights rules, schemas.
- Property: split/merge/ripple/undo invariants, time conversion, dependency graph acyclicity.
- Contract: all engine/provider adapters pass the same success, timeout, malformed, cancellation, and provenance tests.
- Integration: FFprobe -> proxy -> ASR -> translation -> TTS -> timing -> mix -> subtitle -> render.
- Media golden: VFR/CFR, rotation, HDR flags, multichannel audio, embedded subtitles, damaged streams.
- GPU: cold/warm loads, OOM, cancellation, restart, precision, multi-GPU placement.
- UI: keyboard flows, accessibility, project lifecycle, timeline editing, background-job responsiveness.
- Recovery/chaos: kill every process at every artifact/database boundary, disk full, moved source, corrupt cache.
- Security: hostile archives/subtitles/media, secret/log leakage, offline network-deny, signature/hash rejection.
- Packaging: clean supported Windows VMs, repair, upgrade, rollback, uninstall, preserved projects.
- Quality regression: fixed benchmark pack plus blinded human review.

### 16.2 Release blockers

- any original-media mutation
- project corruption or unrecoverable migration
- secret in logs/support bundle
- network traffic in Offline mode
- rights bypass for protected voice generation/export
- critical terminology not flagged
- silent Cinema-mode downgrade
- corrupt/unplayable export reported as success
- UI deadlock during supported long jobs
- blocking quality regression against the approved baseline

## 17. Delivery plan

Durations assume a 12-18 person cross-functional team and parallel workstreams. They are planning ranges, not guarantees.

### Phase 0 - Product and technical proof, 4-6 weeks

Deliver:

- versioned PRD and release boundary
- corrected specification and requirement traceability
- UX workflows/prototypes with five representative professional users
- rational-time and project schema ADRs
- 100,000-item accelerated timeline prototype
- playback/conform A/B prototype
- worker IPC, crash, cancellation, and OOM prototype
- English/Bengali/Hindi model benchmark v0
- license/rights matrix
- packaged UI plus one GPU worker on clean Windows

Exit gate:

- architecture review passes
- no unowned P0 requirement
- playback/timeline prototype meets provisional SLO
- at least one commercially viable ASR, diarization, and voice route exists
- release estimate is re-baselined from measured data

### Phase 1 - Platform foundation, 8-10 weeks

Deliver:

- repository/tooling/CI
- signed contract schemas
- desktop shell and workspaces
- project catalog, project DB, migrations, locks
- artifact store/cache/invalidation v1
- job DAG, supervisor, IPC, checkpoint/recovery
- settings, Credential Manager integration, structured logs
- FFprobe/FFmpeg wrapper and diagnostics

Exit gate:

- create/open/close/recover/relink project
- background media job cannot freeze the UI
- forced worker/UI termination recovers without corruption
- migration and cache invariants pass

### Phase 2 - Media and transcript vertical slice, 8-12 weeks

Deliver:

- import/conform/proxy/thumb/waveform
- viewer/playback controls
- VAD/ASR/word alignment adapter
- transcript correction/lock/version workflow
- source subtitle import and SRT/VTT export
- source-analysis progress and confidence UI

Exit gate:

- short and two-hour fixtures import correctly
- transcript edits persist and do not rerun unrelated analysis
- ASR quality/speed baseline is published by language/hardware

### Phase 3 - Speakers, translation, voice, and timing, 12-16 weeks

Deliver:

- diarization/overlap and manual split/merge
- character and voice-rights registry
- glossary, translation memory, scene context
- official OpenAI/Gemini/DeepSeek plus local provider adapters
- strict structured validation, routing, quotas, circuit breakers
- voice adapter/takes, pronunciation and performance controls
- forced alignment and bounded timing fitter

Exit gate:

- licensed short film completes source -> translated voice takes
- three providers can be individually disabled
- no provider outage prevents manual work/project access
- voice generation/export enforces consent
- selected languages meet approved benchmark thresholds

### Phase 4 - Professional audio, subtitles, QC, export, 12-16 weeks

Deliver:

- M&E selection and separation adapter
- scene/dialogue buses and non-destructive audio chain
- sample-accurate placement, automation, loudness/true-peak analysis
- subtitle editor and reading-speed/line-break QC
- audio/translation/timing/voice QC
- render queue, MP4/MKV/MOV and stem deliverables
- export preflight and post-render validation

Exit gate:

- 60-minute and two-hour projects render, restart, and resume
- approved audio presets pass measurable delivery rules
- exports play in the agreed player/NLE matrix
- disk-full and FFmpeg-failure tests do not corrupt projects

### Phase 5 - Professional timeline and interchange, 14-18 weeks

Deliver:

- complete dubbing timeline toolset and keyboard model
- source/dub/compare, audio scrub, markers, workspaces
- command undo/redo and edit versions
- QC heatmap and batch actions
- partial render graph
- OTIO plus tested stem/subtitle/cue-sheet handoff
- accessibility and high-DPI pass

Exit gate:

- Pro-system UI SLOs pass on two-hour/large-utterance project
- changing one line invalidates exactly the expected artifacts
- professional editor completes a scripted job without engineering help
- interchange round-trip differences are documented and within policy

### Phase 6 - Selective visual dubbing, 10-14 weeks

Deliver:

- shot/face/visibility/active-speaker analysis
- eligibility and manual override
- preview and final lip-sync adapters
- before/after/overlay comparison
- automatic artifact rejection and original-shot fallback
- visual QC and partial visual render

Exit gate:

- no visual failure blocks the audio dub
- high-priority test shots pass objective and blinded-human gates
- wrong-face, occlusion, rapid-cut, and off-screen cases are safe
- full video is not regenerated for one changed shot when the chosen output path supports partial replacement

### Phase 7 - Production hardening and GA, 12-16 weeks

Deliver:

- model/engine package manager
- signed installer/updater/rollback
- offline packs and network-deny verification
- diagnostics/support workflow
- complete threat model, SBOM, license notices, redaction audit
- localization, accessibility, performance, soak, and clean-VM tests
- operations runbooks, support policy, backup/archive guidance
- closed beta and release-candidate benchmark

Exit gate:

- Definition of Done in section 18 passes
- no open severity-1 issue
- severity-2 exceptions have signed release waivers
- model/provider/license inventory is approved
- support and rollback procedures are exercised

### Phase 8 - Studio and general NLE expansion, 12-36+ months

Deliver in separate increments:

- remote/multi-GPU workers and scheduling
- shared PostgreSQL/object storage service
- project checkout/locking or collaboration model
- review tasks, approvals, RBAC/SSO, admin policy, fleet deployment
- creator editing wave, then advanced NLE wave
- plugin SDK after security and ABI governance are mature

Full CapCut/Premiere breadth should be treated as a 3-5 year program with 30-60+ staff, not as the release-1 estimate.

## 18. Production Definition of Done

GA requires all of the following:

- A two-hour project opens, closes, migrates, and resumes without recomputing valid completed stages.
- The UI remains responsive during every supported analysis, model, provider, mix, lip-sync, and render job.
- Frame/sample time invariants and VFR conform tests pass.
- Every AI decision can be inspected and the supported editorial decisions can be manually overridden.
- A single-line change performs proven dependency-limited regeneration.
- Every cloud provider can be disabled; manual/local workflows still open and edit projects.
- Official provider outputs are locally schema/semantically validated and fully failure-tested.
- Model, prompt, provider, engine, hardware, settings, inputs, and output hashes are recorded.
- Voice/reference processing and final export enforce rights policy.
- Offline mode passes OS-level traffic capture tests.
- Export preflight and post-render verification pass for the supported matrix.
- Quality benchmarks have no blocking regression and human release review is complete.
- Crash, power-loss simulation, worker kill, corrupted cache, and disk-full tests preserve source/project integrity.
- Signed install, repair, update, rollback, and uninstall work on clean supported Windows systems.
- Secrets/redaction, threat model, dependency/license, SBOM, and code-signing reviews pass.
- User/admin/support documentation and recovery runbooks are shipped.

## 19. Team and governance

Recommended initial team:

- 1 product lead with localization/dubbing experience
- 1 principal architect/engineering lead
- 3-4 desktop/timeline/media engineers
- 2-3 ML inference/platform engineers
- 1-2 audio/DSP engineers
- 1 video/vision engineer
- 2 product designers, including pro-editor UX
- 2-3 QA/SDET/performance engineers
- 1 release/DevOps engineer
- fractional security/privacy/legal/license specialists
- contracted Bengali/Hindi/English translators, dubbing directors, actors, and audio reviewers

Governance:

- Architecture Decision Records for irreversible/high-cost choices.
- Named owner and success metric for every P0 requirement.
- Weekly risk and dependency review.
- Model/provider promotion board with engineering, quality, product, and legal approval.
- Monthly packaged end-to-end demo on reference hardware.
- No milestone accepted from screenshots or unit tests alone.

Indicative schedule:

- first usable vertical slice: 4-6 months
- controlled audio-dubbing alpha: 8-11 months
- professional editor beta: 12-16 months
- production GA with selective visual dubbing: 18-24 months
- a 4-6 person team should expect roughly 30-42 months for the same GA scope

## 20. Major risks

| Risk | Control |
| --- | --- |
| Scope expands to full Premiere clone | Freeze dubbing-first GA boundary; use interchange; manage NLE expansion as a separate program |
| Python/UI hot paths miss frame-rate target | Qt Quick scene graph, native playback/media runtime, Phase 0 100k-item benchmark, profiler budgets |
| Bengali/Hindi quality is inadequate | Licensed language-specific benchmark, human review, adapter competition, no universal default |
| TTS/model license blocks commercial use | Weight-level and transitive license gate before model promotion |
| Provider API instability/outage | Official APIs, adapters, schema validation, circuit breakers, local/manual fallback |
| GPU/driver fragmentation | Published compatibility matrix, separate engine packs, hardware tiers, OOM/restart tests |
| Separation or lip-sync damages content | Prefer M&E, selective processing, A/B, measurable QC, original fallback |
| Long-job data loss | single writer, atomic publication, immutable artifacts, checkpoints, chaos testing |
| Untrusted media/model compromises workstation | restricted workers, signed packages, safe formats, security fuzz/hostile fixtures |
| Disk growth makes projects unusable | preflight estimates, content-addressed dedupe, quotas, reachability cleanup, archive workflow |
| Installer/update breaks production | signed channels, clean-VM matrix, rollback, project schema compatibility policy |
| "Fastest" drives silent quality loss | quality gates precede speed ranking; publish both quality and real-time factor |

## 21. First 30 days

Week 1:

- initialize repository, ownership, CI, coding/security standards
- normalize and version the specification
- create PRD, traceability matrix, and P0/P1/P2 boundary
- commission legal review of provider/model/voice/content rights
- define reference hardware and benchmark media

Week 2:

- prototype Qt Quick timeline with 100,000 visible/logical items
- prototype playback, proxy mapping, source/dub switching, and precise seek
- prototype project DB, rational time, artifact publication, and crash reconciliation

Week 3:

- prototype worker IPC/supervision, cancellation, GPU discovery, and forced OOM recovery
- benchmark ASR, diarization, TTS, separation, and lip-sync candidates on owned English/Bengali/Hindi fixtures
- build official-provider structured-output contract tests

Week 4:

- package the UI plus one media and one GPU worker on a clean Windows VM
- run security/privacy/network-deny spike
- publish measured architecture decisions, license matrix, risk register, cost model, and re-baselined roadmap
- hold formal Go/No-Go review for Phase 1

## 22. Primary technical references checked

- [Qt Quick Scene Graph](https://doc.qt.io/qtforpython-6.10/overviews/qtquick-visualcanvas-scenegraph.html)
- [OpenTimelineIO](https://github.com/AcademySoftwareFoundation/OpenTimelineIO)
- [FFmpeg filters and loudnorm](https://www.ffmpeg.org/ffmpeg-filters.html)
- [faster-whisper](https://github.com/SYSTRAN/faster-whisper)
- [pyannote.audio](https://github.com/pyannote/pyannote-audio)
- [OpenAI Responses API migration guidance](https://developers.openai.com/api/docs/guides/migrate-to-responses)
- [OpenAI Structured Outputs](https://developers.openai.com/api/docs/guides/structured-outputs)
- [Gemini Structured Outputs](https://ai.google.dev/gemini-api/docs/structured-output)
- [DeepSeek JSON Output](https://api-docs.deepseek.com/guides/json_mode/)
- [Chatterbox](https://github.com/resemble-ai/chatterbox)
- [F5-TTS license statement](https://github.com/SWivid/F5-TTS)
- [MuseTalk](https://github.com/TMElyralab/MuseTalk)
- [LatentSync](https://github.com/bytedance/LatentSync)
- [Demucs maintenance notice](https://github.com/facebookresearch/demucs)
- [Windows credential guidance](https://learn.microsoft.com/en-us/windows/win32/secbp/handling-passwords)
- [C2PA Content Credentials specifications](https://spec.c2pa.org/about/)

## 23. Final recommendation

Approve Phase 0 only. Do not begin the full feature backlog until the timeline/playback, worker isolation, commercial model path, Bengali/Hindi quality, and packaged-GPU-runtime risks have measured answers.

The credible route to an enterprise product is a narrow, excellent, recoverable dubbing workstation first; professional interchange and editor ergonomics second; selective visual AI third; and broad NLE/studio capabilities as separately funded expansions.
