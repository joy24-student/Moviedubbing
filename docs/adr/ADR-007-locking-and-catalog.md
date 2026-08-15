# ADR-007: OS-backed project locks and a separate application catalog

- Status: Accepted
- Date: 2026-08-14
- Owners: Desktop Platform and Storage Infrastructure
- Decision scope: Phase 1 multi-instance safety and project discovery

## Context

An `.aidub` project owns a local SQLite database and immutable media artifacts. SQLite serializes its
own transactions, but it cannot prevent two complete desktop application instances from concurrently
making higher-level editorial decisions, running duplicate jobs, or racing project recovery. The
application therefore needs an exclusive, advisory project ownership protocol that works on Windows
and POSIX development/automation hosts.

Project discovery has a different lifecycle. Recent-project and pinned-project state belongs to the
current OS user and must remain available before any individual project is opened. Putting that state
inside a project database creates a circular discovery dependency, while putting editorial data in a
global database damages portability and data-residency boundaries.

Lock recovery is safety-sensitive. A process identifier can be reused, remote-host PIDs cannot be
checked locally, clocks can be wrong, and a healthy render can outlive an arbitrary age threshold.
Neither PID existence nor lock-record age is proof that a project can be taken over.

## Decision

### Project lock protocol

Every editable project uses two hidden, non-recursive protocol files in its project root:

```text
Movie.aidub/
  .aidub.lock          # stable one-byte OS-lock gate; retained between sessions
  .aidub.lock.json     # atomically published owner record; present only while owned/orphaned
```

The gate and record are deliberately separate. POSIX `flock` and Windows `msvcrt.locking` attach to
an open file/inode. Atomically replacing that same file would let a contender open the new inode and
bypass the original lock. The stable gate is therefore never replaced or routinely deleted. Its first
byte receives a non-blocking exclusive OS lock. A process-local registry also rejects contention
between separate `ProjectLock` objects, independent of platform-specific same-process OS semantics.

After acquiring the gate, the owner atomically publishes a UTF-8 JSON record containing:

- format version;
- operating-system process ID;
- hostname;
- UTC RFC 3339 start timestamp;
- cryptographically random 128-bit nonce encoded as 32 lowercase hexadecimal characters.

Publication writes a same-directory temporary file, flushes and fsyncs it, then performs an atomic
replace and persists directory metadata where the OS exposes directory fsync. Paths must be absolute.
The project root, gate, and record are checked as regular, non-link/non-reparse paths; no recursive
filesystem operation is part of locking.

Normal release checks that the on-disk record still contains the owner's nonce, removes the record
while the gate is held, and then unlocks/closes the gate. Release is idempotent. Context-manager exit
uses the same release operation. If record cleanup fails, the OS handle is still released and the
remaining record becomes an explicit recovery case rather than a leaked live lock.

The possible snapshots are:

| State | OS gate | Valid record | Meaning/action |
| --- | --- | --- | --- |
| `UNLOCKED` | Free | Absent | Normal acquisition is allowed |
| `HELD` | Locked | Present or temporarily absent | Another compliant owner is active; do not break |
| `ORPHANED` | Free | Present | Prior owner did not release cleanly; guarded break is required |
| `INVALID` | Unknown/free | Malformed or unsafe | Preserve evidence and require diagnosis; never overwrite |

Inspection is only a diagnostic snapshot and can race with subsequent acquisition. The OS lock—not
the record's PID, hostname, timestamp, or apparent process liveness—is the authority for active
ownership.

### Guarded break

There is no automatic stale-lock deletion and no lock stealing based on process existence or age.
An administrative break:

1. requires the exact nonce returned by a prior inspection;
2. reserves the lock in the current process and non-blockingly acquires the OS gate;
3. refuses immediately if the gate remains locked;
4. re-reads and validates the record and nonce while holding the gate;
5. calls a required audit hook with the old owner record, project path, breaker PID/hostname, UTC
   timestamp, and non-empty operator reason;
6. aborts without deletion if the audit hook fails;
7. revalidates the nonce, removes only `.aidub.lock.json`, and releases the gate.

This cannot forcibly unlock another process's OS handle. It only removes a provably orphaned record
after explicit, nonce-guarded authorization. The application layer should connect the hook to its
durable security/editorial audit sink before exposing the action in diagnostics UI or CLI.

### Application project catalog

The application catalog is an independent per-user SQLite database, normally located below
`%LOCALAPPDATA%/AIDubStudio` on Windows or the XDG data directory on POSIX. It is never placed inside
an `.aidub` project and never stores project edits, jobs, artifacts, media, credentials, rights
records, or provider content.

Schema version 1 stores one `recent_projects` row per project:

- stable `project_id`;
- canonical absolute `.aidub` directory path plus an OS-normalized uniqueness key;
- Unicode project name;
- UTC last-opened timestamp;
- pinned flag;
- creation/update timestamps.

The catalog enables foreign keys, WAL, `synchronous=FULL`, and a bounded busy timeout. Writes use a
process-local single-writer lock plus short `BEGIN IMMEDIATE` transactions; SQLite supplies the
cross-process writer boundary. Read connections are URI read-only and `query_only`.

The database header uses both a product-specific `application_id` and `PRAGMA user_version`. A new
empty database is initialized transactionally. A non-empty version-zero database, a version-one
database with the wrong application ID/tables, invalid SQLite, or a schema newer than supported is
refused before a writable connection is opened. This prevents a catalog path mistake from adopting or
modifying an unrelated database. Integrity and foreign-key checks run after initialization.

Catalog writes accept only normalized absolute `.aidub` paths. Existing paths must be non-link regular
directories; an explicit `require_exists=False` option is required to retain an offline/moved project.
Health inspection reports available, missing, non-directory, unsafe-link, and invalid path states
without traversing or mutating a project. Removing a recent-project entry deletes only its SQLite row;
it never removes project files.

## Consequences

Positive consequences:

- Two application processes cannot compliantly edit/recover the same project concurrently.
- Same-process contention behaves consistently on Windows and POSIX.
- A crash produces an explainable orphan record rather than silent ownership takeover.
- Administrative recovery is compare-and-delete guarded and externally auditable.
- Recent/pinned discovery remains fast and available without opening project databases.
- Project packages stay portable and isolated from per-user UI state.
- Unicode names and paths support international productions without locale-derived identifiers.

Costs and limitations:

- Advisory locks protect only cooperating processes; they are not an authorization/security boundary
  against software that ignores the protocol.
- Network filesystems may implement Windows byte locks or POSIX flock differently. Shared editing is
  not supported by this local-project protocol and requires the future team-storage architecture.
- A crash after record publication intentionally requires an explicit audited break, even when the
  recorded PID appears dead.
- The stable gate file remains in the project directory. It contains no owner or secret data.
- An inspection result can become stale immediately; acquire/break always re-check under the OS gate.
- The catalog may retain missing paths by explicit request; UI must present its typed health result.

## Alternatives considered

- Lock only SQLite: rejected because project ownership spans files, jobs, artifacts, recovery, and
  editor decisions outside one database transaction.
- Use only `O_EXCL` lock-file creation: rejected because crashes leave a file with no authoritative
  way to distinguish a live owner from an orphan.
- Replace the locked file with each owner record: rejected because replacement changes the locked
  inode/handle and can allow concurrent ownership.
- Delete a lock when its PID is absent or it is “old”: rejected because PID reuse, host boundaries,
  clock errors, suspend, and legitimate long jobs make those heuristics unsafe.
- Permit a force-break of an active OS lock: rejected. The stdlib mechanisms do not safely transfer
  another process's lock, and doing so would violate the single-owner invariant.
- Store the project catalog in every project: rejected because discovery would require finding and
  opening every project first.
- Store project data in the application catalog: rejected because it couples unrelated projects and
  breaks package portability, recovery isolation, and residency boundaries.

## Verification

The lock suite verifies record fields, idempotent context/release behavior, same-process contention,
two spawned-process contention, active-break refusal, forced child-process crash, orphan inspection,
wrong-nonce rejection, successful audited break, audit failure preservation, malformed-record
preservation, and path/link safety where host permissions allow symlink creation.

The catalog suite verifies idempotent initialization, WAL/foreign-key/read-only pragmas, application
and schema identity, Unicode names/paths, pinned ordering, project moves, path collision rollback,
explicit missing-path registration and health, non-destructive row removal, path/link validation,
newer/unrecognized database refusal without data loss, concurrent writer serialization, and SQLite
integrity.

