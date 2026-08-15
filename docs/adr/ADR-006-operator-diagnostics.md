# ADR-006: Local operator CLI and diagnostics contract

- Status: Accepted
- Date: 2026-08-14

## Context

Desktop workstations, render nodes, CI agents, and support engineers need the same deterministic
way to determine whether the application package, localization resources, FFmpeg runtime, and
optional Qt desktop runtime are usable. Startup failures must be understandable without a Python
traceback. Automation also needs a versioned JSON contract and stable exit codes.

Project creation is a rights-sensitive operation. A convenience command must not bypass the domain
authorization record, crash-safe package publication, migration checks, startup recovery, or
artifact reconciliation already enforced by the application layer.

## Decision

Provide a stdlib `argparse` boundary through `python -m aidub` with these commands:

- `doctor` emits either a concise human report or schema-versioned JSON. It performs local checks
  only. Missing FFmpeg, ffprobe, or PySide6 is reported as data; `doctor` fails only when the
  operator explicitly supplies `--require-runtime` and the media runtime is not operational.
- `project create` requires an operator identity and authority basis, constructs the typed source
  authorization record, and delegates publication to `ProjectPackageService`.
- `project validate` delegates migration, interrupted-job recovery, and immutable-artifact
  reconciliation to `ProjectPackageService`, then reports every recovery and reconciliation list.
- `media probe` delegates to the bounded `MediaProbe` adapter and preserves exact rational stream
  rates in JSON as numerator/denominator objects.
- `gui` loads the PySide6 application only after command dispatch, preserving a useful headless CLI
  when the optional native dependency is absent or damaged.

Handlers receive explicit dependency seams and output streams. Tests can therefore exercise the
real parser and serialization contract without launching native processes or the desktop event
loop. The diagnostics collector does not inspect credential stores, environment secrets, project
content, or network services, and it makes no cloud calls.

Exit codes are `0` for success, `1` for an operational command failure, `2` for CLI or desktop
startup usage/dependency errors, `3` for an explicitly required but unavailable media runtime, and
`4` for a project whose artifact reconciliation requires attention.

## Consequences

Support bundles and deployment health checks can consume the same stable report used by humans.
Headless operations remain available independently of Qt. Rights acknowledgments and package
recovery cannot drift into a second CLI-specific implementation. New diagnostics must remain
local, bounded, JSON-compatible, and free of secret values; changing field semantics requires a
diagnostic schema-version increment.
