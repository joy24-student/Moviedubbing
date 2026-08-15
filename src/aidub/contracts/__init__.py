"""Versioned contracts shared by the UI, orchestrator, and workers."""

from .events import EventEnvelope, EventType
from .jobs import (
    ArtifactExpectation,
    JobDescriptor,
    JobError,
    JobProgress,
    JobResult,
    ResourceRequest,
)
from .providers import (
    ProviderCapability,
    ProviderHealth,
    ProviderRequest,
    ProviderResponse,
)
from .worker_ipc import (
    CURRENT_IPC_PROTOCOL_VERSION,
    GpuCapabilitySpec,
    GpuOomPayload,
    IpcMessageType,
    WorkerIpcEnvelope,
)
from .workers import (
    ProtocolVersion,
    WorkerCapability,
    WorkerHandshake,
    WorkerHeartbeat,
)

__all__ = [
    "CURRENT_IPC_PROTOCOL_VERSION",
    "ArtifactExpectation",
    "EventEnvelope",
    "EventType",
    "GpuCapabilitySpec",
    "GpuOomPayload",
    "IpcMessageType",
    "JobDescriptor",
    "JobError",
    "JobProgress",
    "JobResult",
    "ProtocolVersion",
    "ProviderCapability",
    "ProviderHealth",
    "ProviderRequest",
    "ProviderResponse",
    "ResourceRequest",
    "WorkerCapability",
    "WorkerHandshake",
    "WorkerHeartbeat",
    "WorkerIpcEnvelope",
]
