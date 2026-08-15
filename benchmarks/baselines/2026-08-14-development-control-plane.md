# Development control-plane measurement — 2026-08-14

Status: development evidence only; not an approved product baseline  
Machine fingerprint: `6c08623d9a6757f63b8cbb4aaac54c1e1b9de4cbee99e1cbd08b1e7f47f2cf65`  
Runtime: CPython 3.12.10, Windows, AMD64, 4 logical CPUs  
Protocol: 1 warmup, 5 measured repetitions

## Result

| Workload | Median | p95 | Aggregate throughput | Provisional gate |
| --- | ---: | ---: | ---: | --- |
| Original entity-allocation rational-time path, 100k items | 12,001.84 ms | 12,284.40 ms | 8,288 items/s | Fail |
| Precomputed integer `TickRescaler` path, 100k items | 114.14 ms | 118.66 ms | 916,287 items/s | Pass |
| Job DAG construction/traversal, 10k jobs | 6,426.85 ms | 6,712.35 ms | 1,541 items/s | Pass |

The first run failed all rational-time tripwires. The implementation was not accepted as-is and no
threshold was relaxed. The revised architecture validates `RationalRate`/`RationalTime` at domain
boundaries, precomputes the reduced source-to-target integer ratio once, and applies it to bulk tick
arrays without a Pydantic/Fraction allocation per item. Tests verify that bulk results match entity
conversion, including negative ticks and explicit rounding for lossy clocks.

The before/after workload has the same exact NTSC-frame to 48 kHz sample round-trip invariant, but
the new workload deliberately represents the intended accelerated bulk path instead of repeatedly
constructing persistence/editorial entities. This result does not measure playback, drawing,
FFmpeg, GPU work, ASR, translation, voice, or end-to-end UI latency.

## Promotion blockers

- Repeat with seven or more samples on every named reference hardware tier under controlled power
  and thermal conditions.
- Add the 100,000-item Qt timeline/view benchmark and two-hour project fixture.
- Record application commit/build identity in promoted reports.
- Review memory, UI-frame p95, cancellation, and soak results alongside throughput.
- Keep this development record when a promoted baseline replaces it; do not rewrite history.
