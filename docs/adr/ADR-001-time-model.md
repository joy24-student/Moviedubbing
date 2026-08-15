# ADR-001: Exact video and audio time model

- Status: Accepted
- Date: 2026-08-14
- Owners: Timeline, Media, Audio, and Project Platform

## Context

The editor must preserve frame-accurate video decisions and sample-accurate audio placement across
long-form projects, multiple frame rates, proxy/original media, VFR conform, subtitles, generated
speech, mixing, and interchange. Millisecond integers cannot express rates such as 24000/1001
exactly. Binary floating-point seconds accumulate error and make cache keys, range comparisons, and
round trips nondeterministic.

FFmpeg source timestamps, editorial time, and audio clocks also mean different things. Treating all
of them as an unlabelled number creates subtle sync defects, especially at NTSC-derived frame rates
and after repeated conversions.

## Decision

Canonical video/editorial time is `RationalTime`:

```text
RationalTime(ticks: integer, rate: positive rational ticks-per-second)
seconds = ticks * rate.denominator / rate.numerator
```

For example, frame 100 at 23.976 fps is stored as `ticks=100, rate=24000/1001`. The rate is reduced
on construction. Signed rational times are permitted because decoded source PTS can be negative;
persisted `TimeRange` edit boundaries are non-negative.

Canonical audio placement is `AudioSamplePosition(sample_index, sample_rate)`. Its range stores an
integer `sample_count`. It does not use video frames or milliseconds. The project working sample
rate is explicit, normally 48 kHz.

All ranges are half-open `[start, end)`. A range stores start plus duration, requires one time base,
and rejects negative or inverted values. Adjacent ranges therefore do not overlap, and duration is
always `end - start`.

Conversions follow these rules:

1. Exact rescaling is the default. If the target clock cannot represent a value, conversion fails.
2. A potentially lossy conversion requires the caller to name `floor`, `ceil`, `toward_zero`, or
   `nearest_even` explicitly.
3. Range rescaling converts both endpoints and derives the new duration. It never independently
   rounds start and duration, which could move the end twice.
4. Comparison uses exact rational arithmetic. Float seconds are allowed only in ephemeral display or
   telemetry code, never in persisted edit state, contracts, cache keys, or render decisions.
5. Drop-frame and non-drop-frame timecode are formatting/parsing policies. They do not change the
   stored time value.

The following clocks remain distinct fields in higher-level schemas:

- demuxed source PTS/DTS and its stream tick rate;
- conformed source time;
- project edit time;
- project audio sample time;
- generated-artifact local time.

Variable-frame-rate sources require a persisted conform map that associates decoded source frame
PTS with the selected constant-rate edit frames. The media layer must not infer this mapping again
during every render. Proxy generation and relinking must verify that the same map still applies.

## Invariants and database representation

- Rational rate numerator and denominator are positive 32-bit integers and stored reduced.
- Tick and sample positions use signed 64-bit database integers; application validation additionally
  rejects negative edit/sample ranges. Import must reject media that exceeds that storage envelope.
- A database time value is stored as ticks, rate numerator, and rate denominator in separate columns,
  with checks for positive rate components.
- A database range stores start ticks and duration ticks plus one rate, with checks for non-negative
  edit start/duration.
- Audio ranges store start sample, sample count, and sample rate with equivalent checks.
- API/IPC JSON uses integer fields. Decimal or float seconds are never an alternate accepted shape.

Python integers are unbounded, so infrastructure adapters are responsible for enforcing the signed
64-bit persistence boundary before a transaction is committed.

## Consequences

Benefits:

- deterministic math and serialization across machines;
- no cumulative millisecond/frame rounding drift;
- exact cache inputs and reproducible partial renders;
- explicit handling of cross-rate and VFR conform decisions;
- direct sample-accurate audio editing.

Costs:

- UI and provider adapters must convert explicitly at their boundaries;
- cross-rate calculations use rational arithmetic and may temporarily choose a higher common tick
  rate;
- conform-map storage is required for VFR sources;
- SMPTE timecode, including drop-frame validation, needs a dedicated presentation module.

## Rejected alternatives

- **Float seconds:** nondeterministic at frame/sample boundaries and unsafe after repeated edits.
- **Integer milliseconds:** cannot represent NTSC-derived frames or individual 48 kHz samples.
- **One global nanosecond clock:** deterministic but does not represent every rational frame boundary
  exactly and obscures source clock semantics.
- **Frames for both media types:** cannot express sub-frame audio edits.
- **FFmpeg PTS everywhere:** each stream has a different time base and PTS is source timing, not the
  editorial model.

## Verification

The time package requires exhaustive examples and property tests for rate reduction, exact
round-trips, signed rounding, comparison, intersection, adjacency, splitting, and audio/video clock
conversion. Media integration tests will add CFR/VFR, negative source PTS, long-duration NTSC, proxy
mapping, and export round-trip fixtures.
