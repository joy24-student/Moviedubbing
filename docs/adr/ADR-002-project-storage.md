# ADR-002: Per-project SQLite database and immutable content-addressed artifacts

- Status: Accepted
- Date: 2026-08-14
- Owners: Platform and Media Infrastructure
- Decision scope: Phase 1 local project persistence

## Context

AI Dubbing Studio must keep multi-hour productions editable across application, worker, and machine
failures. Source media can be hundreds of gigabytes, while project decisions, job checkpoints, rights
events, and provenance require strongly consistent relationships. A worker can fail at any instruction
between producing bytes and committing metadata. Partial output must never look complete, original
media must never be overwritten, and restarting the application must give a deterministic recovery
answer.

The desktop product is local-first and has one authoritative editor process in Phase 1. It must still
support concurrent readers, isolated worker processes, Unicode project metadata for international
productions, UTC timestamps, and later collection/archive workflows. Large binary payloads do not
belong in a relational database.

## Decision

Each active `.aidub` project is a directory containing an independent `project.db` and an artifact
namespace. Project metadata is stored in SQLite through the standard-library `sqlite3` driver. Binary
outputs are stored under an immutable SHA-256 address:

```text
Feature.aidub/
  project.db
  project.db-wal                 # present while SQLite WAL is active
  project.db-shm
  artifacts/
    .staging/
    sha256/
      ba/
        ba7816bf...0015ad
  recovery/
    project.db.schema-vN.<UTC>.bak
```

Paths persisted in the database are normalized POSIX-style paths relative to the project package.
The database stores only catalog/provenance data: content hash, byte length, logical/media types,
dependency edges, engine/model/prompt versions, normalized parameters, hardware and quality facts,
reproducibility classification, and creation identity/time.

### SQLite operating contract

Every connection enables foreign-key enforcement and a bounded busy timeout. Writable connections
also require WAL journal mode, `synchronous=FULL`, a bounded WAL checkpoint interval, and a journal
size limit. Initialization performs both SQLite integrity validation and a foreign-key check.

All mutations use a single writer service and short explicit `BEGIN IMMEDIATE` transactions. A
process-local lock serializes every `ProjectDatabase` instance referring to the same path; SQLite's
write lock serializes accidental writers in other processes. Nested write transactions are rejected.
Inference, network calls, FFmpeg, hashing, and bulk file copies are forbidden while a project
transaction is open. Readers use independent read-only/query-only connections and continue while the
WAL writer commits.

The Phase 1 schema contains:

- `schema_version`: ordered, checksum-pinned migration history;
- `projects`: project identity, settings, state, and revision;
- `jobs` and `job_dependencies`: resumable DAG state, idempotency, resource request, checkpoint,
  progress, retry/error facts, and leases;
- `artifacts` and `artifact_dependencies`: immutable content/provenance records and source graph;
- `audit_events`: append-only security and editorial events.

Database triggers defend append-only audit history, immutable artifact identity/provenance,
same-project dependency edges, and legal job state transitions even if a caller bypasses repository
helpers.

### Migration and compatibility contract

Migrations are UTF-8 SQL files named `NNNN_name.sql` and bundled under the installable
`aidub.infrastructure.persistence/migrations_sql` package path. Root-level migration files are
operator/deployment copies, and tests require byte-equivalent checksums so installed wheels and source
checkouts cannot diverge. Versions must start at one, be unique, and be contiguous. The SHA-256
checksum and name of every applied migration are stored in `schema_version`; changing published
migration history is an integrity failure. Each pending file runs in its own explicit transaction
without `executescript`'s implicit commit behavior.

Before changing an existing supported schema, SQLite's online backup API creates and fsyncs a
timestamped recovery copy. Forward migrations are the only automatic direction. A database with
unrecognized tables but no migration history is never adopted or overwritten. If its schema version
is newer than this application supports, writable initialization fails; diagnostics and a future UI
may still open it through the explicit read-only connection API. Downgrades are never guessed.

### Artifact publication contract

Only the project service publishes final artifacts. Workers return a staged manifest or stream; they
never write a final content address or mutate project tables.

Publication follows this order:

1. Create an unpredictable `.part` file inside `artifacts/.staging` on the destination filesystem.
2. Stream bytes into the stage, flush them, call file `fsync`, close the handle, and persist staging
   directory metadata where the operating system exposes directory fsync.
3. Re-open the regular non-link file and compute SHA-256 and byte length. Reject a mismatch with the
   worker's declared hash/length.
4. Derive `sha256/<first-two-hex>/<full-lowercase-hex>` internally. Callers cannot supply a final
   path. Every component is containment checked and link/reparse-point checked.
5. Atomically create a hard link at the final address. Hard-link creation is same-filesystem,
   no-clobber publication: it either makes the complete fsynced inode visible or reports that the
   address already exists. An existing object is fully revalidated before deduplication is accepted.
6. Remove the staging name, make a newly published object read-only, and persist directory metadata
   where supported.
7. In one short SQLite transaction, insert the artifact, dependency edges, relevant audit event, and
   job checkpoint/state update.
8. Emit terminal job success only after that transaction commits.

`os.replace` is deliberately not used because it can overwrite an immutable object. Staging and
object directories are within one store so hard-link publication never crosses volumes.

### Recovery and reconciliation

Startup performs two independent reconciliations:

- Jobs left in active process-owned states become `FAILED/PROCESS_INTERRUPTED` (or `CANCELLED` when
  cancellation was already in progress), retaining their checkpoint for an explicit retry.
- The artifact reconciler compares the database's expected hash/size inventory with store contents,
  validates content, reports missing/corrupt/unsafe objects, reports valid unreferenced objects as
  orphans, and removes only expired stage files matching the store's generated filename grammar.

Reconciliation never deletes a published content object. Reachability garbage collection requires a
separate retention/trash policy and is outside this decision.

The publication boundaries have deterministic outcomes:

| Failure boundary | Durable result | Recovery action |
| --- | --- | --- |
| Before stage fsync | No published object | Remove expired generated stage |
| After stage fsync, before link | Complete unpublished stage | Resume publication or expire stage |
| After link, before DB commit | Complete unreferenced object | Report/adopt as orphan; never treat job as successful |
| During DB transaction | SQLite rolls back; object remains immutable | Retry idempotent catalog commit or report orphan |
| After DB commit, before success event | Catalog and object are complete | Idempotency key/checkpoint prevents duplicate work |
| Existing address has wrong bytes/size | Publication is rejected | Mark corruption, diagnose storage, restore/regenerate |

### International and enterprise constraints

SQLite text and canonical JSON are UTF-8/Unicode-safe; language and locale identifiers are stored as
data rather than used in filesystem-derived SQL. All generated timestamps are UTC RFC 3339 values.
Project packages can remain on data-residency-approved local storage; this decision makes no network
call and stores no credentials. Rights and identity details belong in audited structured records,
while secrets remain in the operating-system credential store. Shared network editing and multiple
authoritative writers are explicitly deferred to the future team-storage architecture.

## Consequences

Positive consequences:

- Project metadata commits atomically while large outputs remain streamable and deduplicated.
- A crash at any publication boundary is classifiable and recoverable.
- Original and previously published media are not mutated.
- WAL allows responsive editor reads during short metadata commits.
- Per-project databases simplify portability, backup, data residency, and damage isolation.
- Migration checksums and backups make schema evolution auditable.

Costs and limitations:

- SQLite permits only one writer at a time; application services must keep transactions short.
- Atomic no-clobber publication requires hard-link support on the project filesystem.
- Windows does not expose portable directory fsync through `os.open`; file contents are fsynced and
  atomic filesystem operations are used, while recovery reconciliation remains mandatory.
- SHA-256 validation is I/O-intensive for long media and should run in background health scans after
  the mandatory publication-time validation.
- The read-only bit deters accidental writes but is not an adversarial security boundary; validation
  remains authoritative.
- Content-addressed orphans require an explicit later retention/garbage-collection policy.

## Alternatives considered

- Store blobs in SQLite: rejected because multi-gigabyte media would cause oversized WAL files,
  expensive backups, and poor streaming behavior.
- One global application database: rejected because it couples project failure/portability and makes
  data-residency boundaries unclear.
- A monolithic zip/project file during editing: rejected because each autosave rewrites too much data
  and crash-safe random access is poor.
- Plain filename-based outputs: rejected because overwrite races, deduplication, provenance checks,
  and corruption detection become unreliable.
- `os.replace` into the content namespace: rejected because an existing immutable object can be
  silently replaced.
- SQLAlchemy/Alembic at bootstrap: deferred. The Phase 1 schema and migration runner need no external
  dependency and expose typed APIs; a future team/PostgreSQL edition can add an ORM adapter without
  changing the artifact publication contract.
- PostgreSQL now: rejected for the local desktop edition because it adds a service lifecycle and
  packaging burden. It remains the likely authority for a later collaborative edition.

## Verification

Unit and integration suites cover migration idempotency/checksum enforcement, pre-migration backup,
newer-schema refusal/readability, WAL/foreign keys/busy timeout/synchronous mode, rollback and nested
writer behavior, database guards, legal job recovery, deterministic content paths, hash/size mismatch,
deduplication, corruption detection, safe stage cleanup, catalog reconciliation, and the orphan left
by a deliberately failed database commit.
