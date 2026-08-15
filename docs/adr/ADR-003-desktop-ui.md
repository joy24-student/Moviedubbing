# ADR-003: Native multilingual desktop shell

- Status: Accepted
- Date: 2026-08-14
- Decision owners: Desktop Platform and Product Architecture
- Scope: Phase 0 foundation and Phase 1 application navigation

## Context

AI Movie Dubbing Studio is a Windows-first, local-first professional media
application. Its user interface must remain responsive while media and AI work
runs out of process, expose privacy state without ambiguity, support dense
editor workspaces, and be usable by multinational teams. A browser dashboard
does not meet the native docking, keyboard workflow, offline deployment, or
future accelerated-timeline requirements.

The initial shell also needs to run in build, worker and test environments that
do not install desktop dependencies. Importing business or localization code
must never fail merely because Qt is absent.

## Decision

Use PySide6 and Qt Widgets for the native application shell. Use
`QMainWindow` as the stable workspace host and Qt docks as extension points for
the inspector, activity monitor and later editing tools. Performance-critical
viewer and timeline surfaces may be embedded as Qt Quick components in later
phases; they do not change this shell boundary.

The shell starts with four stable destinations:

1. Home for project discovery and recovery.
2. Projects for local project inventory.
3. Jobs for isolated background processing.
4. System status for media, model, GPU, storage and provider readiness.

The connectivity mode and project privacy policy are persistent text-labelled
indicators above every destination. Color reinforces state but is never the
only signal. The secure default is `Offline` plus `Local only`. Service-layer
updates flow through immutable `ShellStatus` snapshots.

Commands are modeled in a framework-neutral registry. Menus, shortcuts,
navigation and the `Ctrl+K` command palette project the same command records.
This supports keyboard-first operation, later shortcut remapping and future
automation without coupling behavior to a button or `QAction`.

Localization is also framework-neutral. UTF-8 JSON dictionaries are shipped
for:

- `en` — English and mandatory fallback catalog;
- `bn-BD` — Bangla for Bangladesh;
- `hi-IN` — Hindi for India.

Locale identifiers are normalized from common OS forms. Lookup follows exact
locale, base language or installed regional variant, then English. Individual
missing strings fall back to English before exposing the stable translation
key. Catalog metadata includes native display name and text direction so future
right-to-left catalogs do not require a shell redesign. Locale changes update
the live window, menus, navigation, docks, pages, status text and accessibility
names.

PySide6 is an optional dependency at the Python import boundary. The pure
command, state and translation modules remain importable in headless workers
and CI. Constructing or launching a desktop component without PySide6 raises a
targeted `DesktopDependencyError`; the console-friendly launcher prints an
installation diagnostic and returns exit code 2.

## Component boundary

```text
QApplication lifecycle
        |
        v
AIDubMainWindow ----> dock extension points
    |       |
    |       +------> Qt actions / menus / command palette
    |                           |
    v                           v
ShellState                CommandRegistry
    |
    +-------------> persistent policy banner

LocaleService ----> all visible/accessibility text
    |
CatalogRepository -> UTF-8 JSON catalogs
```

Qt types stay under `aidub.ui`. Domain, application, worker and infrastructure
packages must not import Qt. Service integration will use typed view models or
events; workers will never mutate widgets directly.

## Accessibility and internationalization rules

- Every state has meaningful text; color alone is insufficient.
- Focusable controls retain a visible focus ring and accessible name.
- Keyboard navigation and commands are first-class interaction paths.
- Translated strings use named placeholders, never concatenated sentence
  fragments.
- Catalog files preserve Unicode and are reviewed as source artifacts.
- Every non-English catalog must maintain the same key set as English in CI.
- A future locale may declare `rtl`; the shell applies the corresponding layout
  direction while media timelines may explicitly retain left-to-right time.
- Dates, numbers, timecode and plural rules will use dedicated formatters when
  those values enter the shell; they must not be hard-coded into translations.

## Security and privacy implications

Changing an interface language never changes project policy or enables
network access. `Connectivity` and `PrivacyMode` are distinct so online health
cannot be confused with authorization. The UI reports policy; enforcement
belongs to the provider/network boundary and requires separate tests. The
desktop defaults communicate the deny-by-default posture before a project is
opened.

No catalog string is executable. Catalog payloads are validated as string-only
mappings with a supported direction and positive schema version. Invalid
translator formatting falls back to visible unformatted text rather than
preventing application startup.

## Consequences

Positive outcomes:

- Native Windows behavior, keyboard handling, accessibility and mature docks.
- A stable shell can host future timeline, mixer and studio panels.
- Headless tests cover commands, status state and fallback semantics without a
  display server.
- Operators get an actionable failure instead of a PySide6 traceback.
- Multinational rollout has explicit catalog ownership and fallback behavior.

Trade-offs:

- Qt binaries increase installer size and require a dedicated packaging lane.
- Translators currently work with JSON rather than Qt Linguist files. This is
  intentional for service reuse but may require translation-platform adapters.
- Full screen-reader, high-DPI, RTL and Windows packaging validation still
  requires UI automation on real Windows runners.

## Verification

Phase 0/1 gates are:

- unit tests for locale normalization, fallback, validation and catalog parity;
- unit tests for command lifecycle, deterministic search and disabled actions;
- unit tests for observable immutable shell status;
- an optional-dependency test that runs without PySide6 or a display;
- an offscreen Qt smoke test when PySide6 is present in the desktop CI lane;
- manual Windows checks for docking, shortcuts, language switching, scaling,
  focus visibility and persistent offline/privacy indicators.

## Follow-up decisions

Separate ADRs must define persisted workspace layouts, shortcut remapping,
Qt Quick timeline embedding, accessibility automation, installer resource
layout and signed language-pack updates. None may bypass the command,
localization or privacy-policy boundaries established here.
