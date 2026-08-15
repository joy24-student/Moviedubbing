"""DPAPI-protected local secret files for Windows desktop installations."""

from __future__ import annotations

import ctypes
import hashlib
import json
import os
import re
import sys
import tempfile
from ctypes import wintypes
from pathlib import Path
from typing import Any

_NAME_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.:-]{0,159}$")
_CRYPTPROTECT_UI_FORBIDDEN = 0x1
_DESCRIPTION = "AI Dubbing Studio credential"


class DpapiUnavailableError(RuntimeError):
    pass


class _DataBlob(ctypes.Structure):
    _fields_ = [
        ("cbData", wintypes.DWORD),
        ("pbData", ctypes.POINTER(ctypes.c_ubyte)),
    ]


def _blob(data: bytes) -> tuple[_DataBlob, object]:
    buffer = ctypes.create_string_buffer(data)
    blob = _DataBlob(
        len(data),
        ctypes.cast(buffer, ctypes.POINTER(ctypes.c_ubyte)),
    )
    return blob, buffer


def _crypt32() -> Any:
    if sys.platform != "win32":
        raise DpapiUnavailableError("DPAPI is available only on Windows")
    return ctypes.windll.crypt32


def protect_data(data: bytes) -> bytes:
    if not data:
        raise ValueError("cannot protect empty data")
    crypt32 = _crypt32()
    input_blob, input_buffer = _blob(data)
    output_blob = _DataBlob()
    result = crypt32.CryptProtectData(
        ctypes.byref(input_blob),
        _DESCRIPTION,
        None,
        None,
        None,
        _CRYPTPROTECT_UI_FORBIDDEN,
        ctypes.byref(output_blob),
    )
    del input_buffer
    if not result:
        raise ctypes.WinError()
    try:
        return ctypes.string_at(output_blob.pbData, output_blob.cbData)
    finally:
        ctypes.windll.kernel32.LocalFree(output_blob.pbData)


def unprotect_data(data: bytes) -> bytes:
    if not data:
        raise ValueError("cannot unprotect empty data")
    crypt32 = _crypt32()
    input_blob, input_buffer = _blob(data)
    output_blob = _DataBlob()
    result = crypt32.CryptUnprotectData(
        ctypes.byref(input_blob),
        None,
        None,
        None,
        None,
        _CRYPTPROTECT_UI_FORBIDDEN,
        ctypes.byref(output_blob),
    )
    del input_buffer
    if not result:
        raise ctypes.WinError()
    try:
        return ctypes.string_at(output_blob.pbData, output_blob.cbData)
    finally:
        ctypes.windll.kernel32.LocalFree(output_blob.pbData)


class DpapiFileSecretStore:
    """Stores one user-bound encrypted blob per logical secret.

    Logical names are hashed so provider/account identifiers are not exposed in
    filenames. DPAPI binds ciphertext to the current Windows user.
    """

    def __init__(self, root: Path | str) -> None:
        self.root = Path(root).expanduser()
        if not self.root.is_absolute():
            raise ValueError("credential root must be absolute")
        if sys.platform != "win32":
            raise DpapiUnavailableError("DPAPI is available only on Windows")

    @staticmethod
    def _validate(name: str, value: str | None = None) -> None:
        if not _NAME_PATTERN.fullmatch(name):
            raise ValueError("invalid credential name")
        if value is not None and not value:
            raise ValueError("credential value must not be empty")

    def _path(self, name: str) -> Path:
        digest = hashlib.sha256(name.encode("utf-8")).hexdigest()
        return self.root / f"{digest}.credential"

    def set(self, name: str, value: str) -> None:
        self._validate(name, value)
        self.root.mkdir(parents=True, exist_ok=True)
        cleartext = json.dumps(
            {"name": name, "value": value},
            ensure_ascii=False,
            separators=(",", ":"),
        ).encode("utf-8")
        encrypted = protect_data(cleartext)
        descriptor, temporary_name = tempfile.mkstemp(
            prefix=".credential.",
            suffix=".tmp",
            dir=self.root,
        )
        temporary = Path(temporary_name)
        try:
            with os.fdopen(descriptor, "wb") as stream:
                stream.write(encrypted)
                stream.flush()
                os.fsync(stream.fileno())
            temporary.replace(self._path(name))
        except BaseException:
            temporary.unlink(missing_ok=True)
            raise

    def get(self, name: str) -> str | None:
        self._validate(name)
        path = self._path(name)
        if not path.exists():
            return None
        payload = json.loads(unprotect_data(path.read_bytes()).decode("utf-8"))
        if payload.get("name") != name:
            raise ValueError("credential identity mismatch")
        value = payload.get("value")
        if not isinstance(value, str) or not value:
            raise ValueError("credential payload is invalid")
        return value

    def delete(self, name: str) -> bool:
        self._validate(name)
        path = self._path(name)
        if not path.exists():
            return False
        path.unlink()
        return True
