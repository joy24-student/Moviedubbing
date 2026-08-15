# ADR-008: Safe, immutable FFmpeg media derivatives

Status: accepted

## Context

Proxy video, thumbnails, and waveform overviews are generated from project
sources before later AI stages can run. Media paths are user-controlled, jobs
can be cancelled, and FFmpeg can fail after writing a partial file. Publishing
directly to a cache or project artifact path would therefore permit command
injection, corrupt partial artifacts, or accidental replacement of verified
bytes.

Frame-rate and time settings must also be reproducible. Binary floating-point
seconds are not a stable source of cache identity for fractional rates such as
24000/1001.

## Decision

Derivative work is split into two audited boundaries:

1. `aidub.media.commands` creates immutable command plans. Every command is an
   argv tuple, the executable is resolved to an existing file, `-nostdin` and
   `-n` are mandatory, output formats are explicit, and no command shell is
   involved. Codec/filter tokens that enter FFmpeg's own mini-languages are
   validated separately.
2. `aidub.media.derivatives` owns process lifetime and publication. Production
   execution uses a new process group/session, hides the Windows console,
   bounds pipe output, enforces a deadline, parses `-progress pipe:1`, and stops
   the process on cancellation, timeout, output overflow, or callback failure.

All products are generated into a unique hidden name in the destination
directory. A product is eligible for publication only after FFmpeg exits zero,
the output is a non-symlink regular file with non-zero length, an optional
FFprobe validator accepts it, its SHA-256 is calculated, and the file is
flushed. Publication uses a same-directory hard link, which atomically creates
the final name only if it does not exist. The staging link is then removed.
Neither `rename` nor `replace` is used because their overwrite behavior differs
between operating systems.

Cache identity is SHA-256 over canonical JSON containing:

- a cache-schema version;
- the full source-content SHA-256;
- FFmpeg identity and version;
- derivative kind and normalized settings; and
- exact rational numerator/denominator values for frame rates and positions.

Paths and temporary names are deliberately excluded. A renamed source with the
same bytes can reuse the same derivative; a setting or engine-version change
cannot silently reuse an old one.

## Consequences

- Spaces, semicolons, dollar signs, parentheses, and similar path characters
  remain literal argv content rather than executable syntax.
- Cancellation and failed validation leave no published artifact. Existing
  output paths, including broken symlinks, are refused before work and again at
  the atomic publication boundary.
- The default validator establishes filesystem integrity; release workflows
  should inject the FFprobe validation seam for codec/stream validation.
- Atomic no-overwrite publication requires a filesystem that supports hard
  links. The staging and final paths are always on the same volume. An
  unsupported filesystem fails closed and retains no final output.
- Cache equivalence is scoped to the declared FFmpeg version and normalized
  settings. Hardware-specific codec output is not claimed to be bit-identical
  unless the artifact provenance separately records an exact reproducibility
  guarantee.
- The first waveform derivative is a deterministic overview PNG. A later editor
  phase may add tiled, multi-resolution peak data without changing this
  publication contract.

## Verification

Unit tests cover exact rational command material, canonical cache keys,
filter-token validation, and typed progress parsing. Integration tests use an
injectable runner and fake executable because FFmpeg is not a required test
host dependency. They prove that untrusted-looking filenames occupy literal
argv elements, cancellation never publishes partial bytes, and pre-existing
targets are never overwritten or passed to a process.
