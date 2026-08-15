# Product requirement traceability

Baseline source: `AI_Movie_Dubbing_Studio_Master_Specification_v2-1.md`, section 58  
Delivery source: `ENTERPRISE_IMPLEMENTATION_PLAN.md`, sections 12, 15–18  
Snapshot date: 2026-08-14

## Status definitions

- **Foundation implemented:** current code/tests satisfy the explicitly described foundation slice;
  later end-to-end or packaged verification may remain.
- **Partial:** some contracts or infrastructure exist, but the complete product requirement and exit
  evidence do not.
- **Pending:** no meaningful implementation of the product behavior exists yet.
- **Blocked evidence:** code may exist, but a mandatory benchmark/license/packaging/quality gate has
  no approved result.

“Implemented” here is repository traceability, not a production certification. Phase exit requires
the integration, packaged-app, media fixture, recovery, security, quality, and rights evidence in the
enterprise plan.

## Functional requirements

| ID | Status | Current implementation/evidence | Remaining delivery |
| --- | --- | --- | --- |
| FR-001 Project lifecycle | Partial | `domain/project.py`; `application/projects.py`; persistence migrations/database; `tests/integration/application/test_project_packages.py` exercises atomic create/open and interrupted-job recovery | Duplicate, archive/collect, relink, full recovery UX, newer-schema read-only behavior and packaged chaos tests; Phases 1–2 |
| FR-002 Media ingestion | Partial | `media/runtime.py`, `probe.py`, `fingerprint.py`, `importer.py`; `domain/media.py`; unit media tests cover typed FFprobe parsing/import | Real legal golden MP4/MKV/MOV fixtures, damaged/VFR/interlaced/HDR validation, attachments and relink workflow; Phase 2 |
| FR-003 Proxy workflow | Partial | `media/commands.py` and `media/derivatives.py` provide deterministic proxy/thumbnail/waveform plans, cancellation/timeout, validation, cache keys and atomic no-overwrite publication; ADR-008 and focused tests | Verified FFmpeg distribution, legal golden fixtures, source/proxy conform map, background-job/UI wiring and original-reference export tests; Phase 2 |
| FR-004 ASR | Partial boundary / blocked evidence | `speech/` provides exact sample-clock chunk planning, provenance-rich contracts, deterministic overlap merge, cancellation/progress seams, and `domain/utterance.py`; benchmark evidence schema captures WER/CER/timing | Commercial ASR adapter, alignment worker/UI, approved `en`/`bn-BD`/`hi-IN` fixtures and measured baselines; Phase 2 |
| FR-005 Diarization | Pending / blocked evidence | Job/provider contracts can carry work; benchmark schema captures DER | Engine adapter, stable speaker model, manual correction workflow, biometric review and approved DER evidence; Phase 3 |
| FR-006 Character memory | Partial schema | Character/speaker IDs and utterance links exist | Character, speaker/face link, pronunciation/style/relationship aggregates and editors; Phase 3 |
| FR-007 Translation | Partial schema / blocked evidence | `domain/localization.py` provides versioned translations/provenance/warnings; provider contracts exist | Context/glossary/memory services, adapters, editor/version workflows and human language benchmark; Phase 3 |
| FR-008 Provider routing | Partial contract / blocked evidence | `contracts/providers.py`; privacy gate in `security/privacy.py`; ADR-005 | Authorized official adapters, rate limits, fallback/circuit breaker, credential/disclosure audit, contract tests, approved terms; Phase 3 |
| FR-009 Voice generation | Partial rights schema / blocked evidence | `domain/rights.py` blocks unconsented/expired/revoked use; voice artifact/profile contracts and tests | Commercially approved engine/weights, synthesis workers, reference pipeline, A/B takes and multilingual quality evidence; Phase 3 |
| FR-010 Performance control | Partial schema | `domain/utterance.py` models emotion, rate, energy and pitch | Engine-neutral pause/emphasis controls, synthesis support, UI and audible regression tests; Phases 3 and 5 |
| FR-011 Timing | Partial foundation | ADR-001 and `domain/time.py` provide exact edit/sample math; benchmark workload exercises conversions | Forced alignment, rewrite/pause/time-stretch policies, timing editor and measured +/-8% quality gate; Phase 3 |
| FR-012 Stem handling | Pending | Stem directories and immutable artifact type exist | Supplied M&E selection, separation adapter, provenance, audible fallback label, mixing integration and rights-approved model; Phase 4 |
| FR-013 Lip-sync | Pending / blocked evidence | No visual pipeline; candidate routes are unverified in the rights matrix | Shot/face/active-speaker eligibility, preview/final adapters, fallback/QC/consent/provenance; Phase 6 |
| FR-014 Timeline editor | Partial foundation | Exact time/range library; precomputed integer `TickRescaler`; measured 100k control-plane transform passes the provisional gate; shell commands/models and revision-safe transcript commands; ADR-001/ADR-003/ADR-010 | Accelerated 100k-item Qt multitrack surface, playback, editing operations, markers/snapping/zoom/solo/mute/lock, undo and interchange; Phase 5 |
| FR-015 QC | Pending / scaffold | QC artifact type and quality evidence schemas exist | Typed issues, translation/voice/timing/pronunciation/audio/lip checks, reviewer workflow and release blocking; Phase 4 onward |
| FR-016 Render queue | Partial platform | Versioned job contracts, canonical domain job state machine, deterministic DAG, worker supervisor/crash test, persistence recovery | Scheduler/resource reservations, pause/resume/checkpoints, GPU/OOM policy, mix/render/export workers and partial rerender; Phases 1 and 4 |
| FR-017 Offline mode | Partial foundation | `security/privacy.py`, project privacy settings and tests fail closed for network policy | Enforce policy at every future provider/telemetry transport plus packaged network-deny tests; Phases 1–3 and 7 |
| FR-018 Model manager | Partial evidence scaffold / blocked evidence | `benchmarks/models.py` records exact engine/model/version/weight hash and metrics; protocol/matrix added | Signed model registry/install/verify/load/unload/remove, disk/VRAM estimates, actual approved benchmark routes and UI; Phases 1, 3 and 7 |
| FR-019 Rights ledger | Partial foundation | `domain/rights.py`; source authorization in project creation; append-only audit persistence; rights tests and matrix | Evidence storage/access UI, expiry/revocation propagation across jobs/final export, provider disclosure ledger and hash-chain policy mode; Phases 1, 3 and 7 |
| FR-020 Diagnostics | Partial foundation | `diagnostics/system.py`, sanitized structured logging/redaction, local doctor CLI, ADR-006 and tests | User-previewed redacted support bundle, minidumps/worker traces, GPU history, opt-in upload and packaged validation; Phase 7 |

## Non-functional requirements

| ID | Status | Current implementation/evidence | Remaining verification |
| --- | --- | --- | --- |
| NFR-001 Responsiveness | Partial | Heavy-work process contract/supervisor; UI shell separated from workers; `TickRescaler` bulk path measured at 114.14 ms median / 118.66 ms p95 for 100k items on the development machine | Long media/GPU job responsiveness, rendered 100k Qt timeline, playback and packaged p95 tests on every reference tier |
| NFR-002 Recoverability | Partial | SQLite WAL/migrations, atomic artifact publication/reconciliation, interrupted-job recovery integration tests | Checkpoints at real stage boundaries, UI/worker kill matrix, disk-full/cache recovery and migration fleet |
| NFR-003 Determinism | Foundation implemented | `domain/artifact.py` provenance/cache material; exact time; immutable artifacts; benchmark schema stores raw samples and exact model/weight identity | Enforce provenance for every future adapter and export; reproducibility qualification on real engines |
| NFR-004 Privacy | Partial foundation | DPAPI-backed credentials, redaction, offline policy and tests; fixture protocol excludes sensitive payloads from results | Transport-wide network deny, malicious input/support-bundle tests, provider DPA/data-flow approval |
| NFR-005 Scalability | Partial contract | Versioned worker/job contracts and DAG decouple editor semantics; resource request schemas | Multi-GPU/local/remote scheduler, backpressure/fairness and shared-store/studio tests |
| NFR-006 Observability | Partial foundation | Event/job contracts, structured logging, diagnostics and benchmark raw timing/throughput evidence | End-to-end trace correlation, GPU/VRAM samples, provider usage/cost and opt-in telemetry policy |
| NFR-007 Quality safety | Partial schema / blocked evidence | Confidence/warnings/status fields and benchmark applicability/approval gate | Review UI, per-task blocking thresholds and approved language/model baselines |
| NFR-008 Accessibility | Partial shell | Keyboard command registry/palette, locale service and shell models/tests | Focus/readability/scalable-text/high-contrast/screen-reader review on packaged UI |
| NFR-009 Compatibility | Partial / blocked evidence | Python 3.12/3.13 Windows/Linux CI matrix, installed-wheel smoke, Windows native desktop CI lane, runtime diagnostics and optional dependency checks | Execute/review hosted evidence, clean Windows 10/11 signed installers, CUDA tiers, codec/HDR/interchange matrix and rollback |
| NFR-010 Maintainability | Foundation implemented | Domain/application/contracts/infrastructure/worker/UI boundaries, strict schemas, hosted quality/package workflows and focused contract/unit/integration tests | Adapter shared suites, ownership/API compatibility policy, dependency lock governance and SBOM automation |

## Phase 0 and Phase 1 deliverable evidence

| Plan deliverable | State | Evidence / gap |
| --- | --- | --- |
| Versioned release boundary and traceability | Partial | Enterprise plan plus this matrix; formal PRD ownership/sign-off still required |
| Rational-time ADR and library | Implemented foundation | ADR-001, `domain/time.py`, property/unit tests and exact-time benchmark workload |
| Project schema/storage ADR | Implemented foundation | `domain/project.py`, ADR-002, persistence and project-package integration tests |
| 100,000-item accelerated timeline | Partial | Precomputed exact integer transform passes the development tripwire at 114.14 ms median / 118.66 ms p95; evidence record retained | This is not a rendered Qt timeline; add multitrack drawing/interaction/frame-pacing and memory evidence on reference tiers |
| Playback/conform A/B prototype | Pending | FFprobe/import exists; playback and VFR conform mapping do not |
| Worker IPC/crash/cancel/OOM prototype | Partial | Contracts, local process supervisor and crash containment exist; authenticated IPC, cooperative cancel/checkpoint and GPU OOM route remain |
| English/Bengali/Hindi model benchmark v0 | Scaffold only / blocked evidence | Schema/protocol/fixture registry exist; no approved fixtures, routes, measurements or human review |
| License/rights matrix | Initial blocking control | All candidate production routes remain UNVERIFIED/BLOCKED/PROHIBITED pending evidence |
| Packaged UI plus GPU worker | Partial | Wheel contains migrations, `py.typed`, and en/bn-BD/hi-IN catalogs; isolated installed-wheel create/validate smoke passes; native Windows desktop CI lane is defined | Hosted clean-machine evidence, signed installer and a packaged GPU worker remain absent |
| Repository/tooling/CI | Foundation implemented | `pyproject.toml`, strict test/lint/type/coverage configuration and Python 3.12/3.13 Windows/Linux quality, package, installed-wheel and desktop-smoke workflows | Hosted branch protection, signing, dependency locking, SBOM and release provenance remain |
| Project DB/migrations/locks | Foundation implemented | WAL/FK/integrity/migration checks, recovery, OS-backed cross-process locks, guarded audited breaks, separate app catalog and project-package integration tests | Full release-to-release migration fixture fleet and recovery UX remain |
| Artifact store/cache/invalidation | Partial | Atomic content-addressed store/reconciliation and graph invalidation exist; production cache service/GC and complete dependency wiring remain |
| Job DAG/supervisor/checkpoint/recovery | Partial | DAG/state/supervisor and DB recovery exist; scheduler leases/checkpoints/resources/remote transport remain |
| Settings/credentials/logs | Partial foundation | Typed settings, DPAPI store, redaction/structured logs and diagnostics exist; UI and support-bundle hardening remain |
| FFprobe/FFmpeg wrapper/diagnostics | Partial foundation | Runtime/probe/import/doctor plus shell-free proxy/thumbnail/waveform commands, bounded cancellation/timeout, structural validation seam and atomic publication exist | Approved FFmpeg package, real encoding fixtures, VFR conform/playback and golden media matrix remain |
| Transcript and speech boundaries | Partial foundation | `transcript/` revision-safe commands and invalidation roots; `speech/` deterministic long-form recognition contracts, chunking, merge warnings, and ADR-010/ADR-011; focused tests included in the full gate | Real ASR/diarization engines, model packs, worker IPC, human review UI, and language-quality evidence remain |

## Evidence maintenance

Every merge that changes a requirement status must update this document in the same change. An item
moves to implemented only with links to code, automated tests, and any required packaged/manual,
benchmark, rights, or security evidence. Missing external evidence is recorded as a blocker; it is
never replaced with an assumed metric or license conclusion.
