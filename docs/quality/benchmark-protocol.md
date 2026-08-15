# Benchmark and quality evidence protocol

Status: Phase 0 scaffold; no production baseline approved  
Schema: `aidub.benchmarks`, version 1  
Applies to: control-plane performance, media/AI engines, providers, prompts, models, and weights

## 1. Purpose and non-claims

Benchmarks exist to make architecture and release decisions reproducible. They are not marketing
claims, legal approvals, or a substitute for professional language review. This repository currently
contains no measured ASR, diarization, translation, voice, timing, lip-sync, or end-to-end quality
result. Unit tests use synthetic values only to validate contracts.

The first accepted baseline must be measured on approved fixtures and published reference machines.
Until then, model routes and provider routes remain unverified and production-blocked.

## 2. Control-plane workload invocation

Run the current standard-library harness without installing a separate CLI entry point:

```powershell
python -m aidub.benchmarks --workload all --output .benchmark-results/phase0.json
```

Item counts, warmups, and repetitions are configurable:

```powershell
python -m aidub.benchmarks `
  --workload rational-time `
  --rational-items 100000 `
  --warmups 2 `
  --repetitions 7
```

The process exits `0` when every configured threshold passes and `2` when any gate fails. Exceptions,
incomplete item counts, and a non-monotonic clock fail the run rather than producing plausible-looking
numbers.

### Current provisional gates

| Workload | Default items | Median | p95 | Aggregate throughput |
| --- | ---: | ---: | ---: | ---: |
| Exact rational-time/frame/sample operations | 100,000 | <= 5,000 ms | <= 7,500 ms | >= 10,000 items/s |
| Job DAG construction, validation, topological traversal, readiness, descendants | 10,000 | <= 7,500 ms | <= 10,000 ms | >= 500 items/s |

These values are source-controlled engineering tripwires, not measurements. They must remain marked
`provisional=true` until the Phase 0 architecture review replaces them with evidence from all named
reference tiers. Tightening or relaxing a gate requires a recorded reason and before/after results.

## 3. Timing and statistics

- Use a monotonic nanosecond clock around the workload only.
- Complete configured warmups before measured repetitions; warmups are not included in statistics.
- Use at least seven repetitions for a promoted CPU/control-plane baseline unless a documented
  workload cost requires more rigorous sampling with fewer repetitions.
- Retain every raw elapsed-nanosecond sample.
- Median is the standard median of measured elapsed times.
- p95 uses the nearest-rank method: sort ascending and select rank `ceil(0.95 * n)`.
- Throughput is total completed logical items divided by total measured time, not an average of
  rounded per-run rates.
- Run on AC power with thermal state stabilized. Record foreground/background process policy,
  performance power mode, and any unavoidable interference in the review record.
- Never remove a slow sample as an “outlier” without preserving both the original result and a
  documented, independently reviewable invalidation reason.

Unit tests inject their clock, workload, timestamps, run ID, and machine data. They never assert
against developer-machine wall time.

## 4. Machine and runtime identity

Every performance result includes a privacy-preserving machine fingerprint derived from operating
system, release, architecture, processor description, pointer width, Python implementation/version,
and logical CPU count. Hostname, username, MAC address, serial numbers, and paths are excluded.

GPU/model benchmarks must additionally record outside the standard-library fingerprint:

- GPU vendor/model/count and stable internal device labels;
- driver, CUDA/ROCm/DirectML runtime, cuDNN/TensorRT/ONNX Runtime as applicable;
- VRAM total/reserved/peak and precision;
- engine environment lock hash, application commit, model package, weight hash, and warm/cold state;
- CPU, RAM, storage class, thermal/power mode, and worker concurrency.

The additional inventory must be sanitized before a support bundle leaves the machine.

## 5. Fixture admission and partitioning

Only fixtures admitted under `benchmarks/fixtures/README.md` may be used. Before each run, verify the
dataset version and canonical manifest SHA-256. License, participant/performer consent, biometric/voice
scope, permitted providers, languages, territories, and retention must all be explicit.

Maintain non-overlapping development, validation, and blinded test partitions. Do not tune prompts,
normalization, thresholds, or models on the blinded test partition. Record duplicate/near-duplicate
checks and contamination risks. Human reviewers must not see engine identity during comparative
rating where practical.

Report English (`en`), Bengali (`bn-BD`), and Hindi (`hi-IN`) independently. Code-switching may have
an additional cohort but may not replace the three language reports. Do not publish only a weighted
aggregate.

## 6. Required model evidence schema

One `ModelBenchmarkEvidence` record identifies exactly one task, language, dataset version, engine,
model, and weight hash. It must declare applicability for all six canonical metrics; absent metrics
are represented as `not_applicable` or `not_measured` with an explanation, never as zero.

| Metric | Definition and required disclosure |
| --- | --- |
| WER | Word edit distance divided by reference word count; publish frozen tokenization and language normalization rules. WER can exceed 1.0. |
| CER | Character/grapheme edit distance divided by reference length; publish Unicode normalization, punctuation, numeral, and script policy. |
| DER | Missed speech + false alarm + speaker confusion divided by scored time; publish collar and overlap-scoring policy. |
| MOS | Blinded human 1–5 opinion score; publish question, scale anchors, listener qualification, sample count, confidence interval, and exclusions. |
| Timing error p95 | p95 absolute error against an approved target boundary/slot in milliseconds; publish alignment and exception rules. |
| Requests/s | Completed valid requests divided by measured service time; publish batch size, concurrency, input distribution, retries, and warm/cold state. |

Metric applicability is task-specific. For example, DER may be not applicable to a pure voice model;
it must still be present with that explanation. Any measured metric requires a timestamp and machine
fingerprint. Numeric JSON with missing rights or identity fields is not valid evidence.

## 7. Task-specific protocol

### ASR and alignment

- Score verbatim and approved normalized forms separately when normalization materially changes the
  language result.
- Preserve named entities and controlled terminology as a separate error slice.
- Report WER and CER for every language; include timing p95 for word/segment alignment.
- Stratify noise, overlap, music, code-switching, utterance length, and confidence bands.

### Diarization

- Publish DER configuration, speaker-count assumptions, overlap handling, and manual oracle inputs.
- Report speaker confusion independently and test stable identity behavior across scenes.

### Translation and adaptation

- Use blinded professional reviewers for adequacy, fluency, terminology, cultural/rating constraints,
  and critical meaning changes.
- Automated metrics may supplement but cannot replace blocking human error categories.
- Report target-slot timing errors after approved text normalization.

### Voice/TTS/voice conversion

- Verify consent/license scope before synthesis—not after listening.
- Use blinded MOS with intelligibility, naturalness, speaker suitability, pronunciation, extra speech,
  clipping, and wrong-character checks.
- Keep identity/similarity metrics restricted where they constitute biometric processing.

### Performance and providers

- Separate client overhead, queue/provider latency, model compute, and end-to-end latency.
- Record throttling, retry, invalid response, repair, cancellation, and cost/usage observations.
- Provider data may be sent only under an approved disclosure policy for that fixture.

## 8. Approval and regression decisions

A route is `approved` only when:

1. Dataset license and required consent are verified for the intended commercial purpose and
   territories.
2. Code, dependency, model, weight, and provider terms are approved in the rights matrix.
3. Required language/task metrics are measured on the blinded partition and pass signed gates.
4. Critical-error review has no unresolved blocker.
5. Security/privacy review approves execution, storage, logging, and provider disclosure.
6. Model governance and the responsible language owner sign the exact evidence ID.

Every engine/model/weight/prompt/default change creates a new evidence record. A regression is never
hidden by switching precision, model, hardware, language mix, or quality preset. Cinema mode cannot
silently downgrade.

Accepted result JSON is immutable. Put it under `benchmarks/baselines/schema-v1/` through review and
advance a separately reviewed index. Failed and invalidated results remain auditable.

## 9. Security and privacy

- Benchmark runners default to local execution and never discover/upload data on their own.
- Logs and result JSON use opaque fixture IDs and exclude transcript/media payloads, secrets, names,
  local paths, provider credentials, and biometric vectors.
- Each run uses bounded scratch storage and staged output; verify and purge per the dataset schedule.
- An expired/revoked grant blocks new runs immediately and triggers the approved affected-evidence
  review process.
- A benchmark pass never overrides a rights, security, privacy, or export-policy block.
