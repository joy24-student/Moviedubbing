# Approved benchmark baselines

This directory is intentionally empty of numerical baselines. The repository currently contains a
runner, schemas, provisional control-plane thresholds, and an evidence protocol—not measured model
or product performance claims.

## Baseline promotion

A result may be added only through a reviewed change containing:

1. The immutable result JSON produced by the benchmark schema version in use.
2. Machine fingerprint and relevant GPU/driver/runtime inventory.
3. Workload configuration, warmup count, repetition count, raw samples, median, p95, and throughput.
4. Fixture dataset ID/version/manifest hash and links to approved license/consent evidence.
5. Engine, model, version, exact weight hash, prompt/configuration, precision, and deterministic seed
   where supported.
6. Per-language metrics with every WER, CER, DER, MOS, timing, and RPS field marked applicable,
   not applicable, or not measured.
7. Reviewer decision from engineering, language quality, model governance, privacy/legal, and
   security as applicable.
8. A comparison against the previous approved baseline and an explanation for every regression.

Baseline filenames should be collision-resistant and non-identifying, for example:

```text
schema-v1/<workload-or-task>/<language>/<engine-model>/<run-id>.json
```

Do not use `latest.json`, overwrite an accepted result, or copy a failing run over history. A small
signed index should identify the currently approved baseline while immutable run files remain
available for audit.

## Interpretation

- The thresholds in `src/aidub/benchmarks/workloads.py` are provisional engineering tripwires.
- A threshold pass is not proof of production readiness, model quality, legal permission, or feature
  completion.
- A model result without verified fixture rights is invalid even if its metrics are excellent.
- A model/provider/weight without an approved license route is production-blocked even if it passes
  a benchmark.
- No cross-language aggregate may hide a failing Bengali, Hindi, or English cohort.

See `docs/quality/benchmark-protocol.md` for execution rules and
`docs/quality/license-rights-matrix.md` for the production gate.
