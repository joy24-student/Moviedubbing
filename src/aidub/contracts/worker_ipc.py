"""Structured, schema-validated IPC protocol for isolated worker processes."""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import Any

from pydantic import Field

from .base import ContractModel, Identifier, utc_now
from .workers import ProtocolVersion, WorkerCapability, WorkerHandshake, WorkerHeartbeat


class IpcMessageType(StrEnum):
    HANDSHAKE = "handshake"
    HANDSHAKE_ACK = "handshake_ack"
    HEARTBEAT = "heartbeat"
    JOB_SUBMIT = "job_submit"
    JOB_PROGRESS = "job_progress"
    JOB_RESULT = "job_result"
    JOB_CANCEL = "job_cancel"
    ERROR = "error"
    SHUTDOWN = "shutdown"


CURRENT_IPC_PROTOCOL_VERSION = ProtocolVersion(major=1, minor=0)


class WorkerIpcEnvelope(ContractModel):
    """Canonical IPC message envelope passed across worker process boundaries."""

    message_id: Identifier
    message_type: IpcMessageType
    sender_id: Identifier
    timestamp: datetime = Field(default_factory=utc_now)
    payload: dict[str, Any] = Field(default_factory=dict)

    def is_type(self, message_type: IpcMessageType) -> bool:
        return self.message_type is message_type


class GpuCapabilitySpec(ContractModel):
    """Specification of GPU capabilities, hardware constraints, and resident models."""

    device_index: int = Field(ge=0)
    device_name: str = Field(min_length=1, max_length=128)
    total_vram_mb: int = Field(gt=0)
    available_vram_mb: int = Field(gt=0)
    supported_capabilities: frozenset[WorkerCapability]
    supported_precisions: tuple[str, ...] = ("float16", "float32")
    loaded_models: tuple[Identifier, ...] = ()


class GpuOomPayload(ContractModel):
    """Structured diagnostic data returned when a GPU worker runs out of VRAM."""

    job_id: Identifier
    device_index: int = Field(ge=0)
    requested_vram_mb: int
    free_vram_mb: int
    loaded_models: tuple[Identifier, ...] = ()
    traceback: str = ""


__all__ = [
    "CURRENT_IPC_PROTOCOL_VERSION",
    "GpuCapabilitySpec",
    "GpuOomPayload",
    "IpcMessageType",
    "WorkerHandshake",
    "WorkerHeartbeat",
    "WorkerIpcEnvelope",
]
