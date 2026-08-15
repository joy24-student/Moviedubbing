# ADR-004: Strict, versioned worker contracts

Status: accepted

## Context

Media and AI engines execute outside the desktop process. Their dependencies,
failure modes, and release cadence differ from the application shell.

## Decision

All process boundaries use immutable, strict Pydantic contracts now and a
wire-compatible Protobuf representation before remote workers are introduced.
Unknown fields are rejected. Each worker performs a protocol handshake, reports
capabilities and heartbeats, and receives immutable job descriptors. Workers do
not write project databases or publish directly into the final artifact store.

## Consequences

- A worker crash cannot corrupt editor memory or project state.
- Contracts need compatibility tests and explicit versioning.
- Large media remains file/artifact referenced rather than copied into IPC.
- The orchestrator persists terminal state before emitting success.

