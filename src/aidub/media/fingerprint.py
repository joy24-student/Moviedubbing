"""Streaming source fingerprints that never mutate input media."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from pathlib import Path

_FAST_BLOCK_BYTES = 1024 * 1024


@dataclass(frozen=True, slots=True)
class SourceFingerprint:
    fast_sha256: str
    byte_length: int
    full_sha256: str | None = None


def _validate_file(path: Path | str) -> Path:
    result = Path(path).expanduser().resolve(strict=True)
    if not result.is_file():
        raise ValueError(f"source is not a regular file: {result}")
    return result


def fast_fingerprint(path: Path | str) -> SourceFingerprint:
    """Hash size plus deterministic head/middle/tail samples.

    This is a quick relink hint, not a cryptographic replacement for the full
    content hash. Artifact provenance must use full_fingerprint.
    """

    source = _validate_file(path)
    size = source.stat().st_size
    digest = hashlib.sha256()
    digest.update(b"aidub-fast-fingerprint-v1\0")
    digest.update(size.to_bytes(16, "big"))
    offsets = sorted(
        {
            0,
            max(0, size // 2 - _FAST_BLOCK_BYTES // 2),
            max(0, size - _FAST_BLOCK_BYTES),
        }
    )
    with source.open("rb", buffering=0) as stream:
        for offset in offsets:
            stream.seek(offset)
            block = stream.read(_FAST_BLOCK_BYTES)
            digest.update(offset.to_bytes(16, "big"))
            digest.update(len(block).to_bytes(8, "big"))
            digest.update(block)
    return SourceFingerprint(fast_sha256=digest.hexdigest(), byte_length=size)


def full_fingerprint(path: Path | str, *, chunk_bytes: int = 8 * 1024 * 1024) -> SourceFingerprint:
    if chunk_bytes < 64 * 1024:
        raise ValueError("chunk_bytes must be at least 64 KiB")
    source = _validate_file(path)
    quick = fast_fingerprint(source)
    digest = hashlib.sha256()
    with source.open("rb", buffering=0) as stream:
        while block := stream.read(chunk_bytes):
            digest.update(block)
    return SourceFingerprint(
        fast_sha256=quick.fast_sha256,
        byte_length=quick.byte_length,
        full_sha256=digest.hexdigest(),
    )
