"""Small framework-neutral models exposed by the desktop shell."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from enum import StrEnum
from threading import RLock


class Connectivity(StrEnum):
    OFFLINE = "offline"
    ONLINE = "online"
    DEGRADED = "degraded"


class PrivacyMode(StrEnum):
    LOCAL_ONLY = "local_only"
    HYBRID = "hybrid"
    CLOUD_ALLOWED = "cloud_allowed"


@dataclass(frozen=True, slots=True)
class ShellStatus:
    """Security-relevant status rendered persistently by the shell."""

    connectivity: Connectivity = Connectivity.OFFLINE
    privacy_mode: PrivacyMode = PrivacyMode.LOCAL_ONLY
    active_project_name: str | None = None
    ready: bool = True


StatusListener = Callable[[ShellStatus], None]


class _Unset:
    __slots__ = ()


_UNSET = _Unset()


class ShellState:
    """Observable shell state that is safe to update from service callbacks."""

    def __init__(self, status: ShellStatus | None = None) -> None:
        self._status = status or ShellStatus()
        self._listeners: list[StatusListener] = []
        self._lock = RLock()

    @property
    def status(self) -> ShellStatus:
        with self._lock:
            return self._status

    def replace(self, status: ShellStatus) -> None:
        if not isinstance(status, ShellStatus):
            raise TypeError("status must be a ShellStatus instance")
        with self._lock:
            if status == self._status:
                return
            self._status = status
            listeners = tuple(self._listeners)
        for listener in listeners:
            listener(status)

    def update(
        self,
        *,
        connectivity: Connectivity | _Unset = _UNSET,
        privacy_mode: PrivacyMode | _Unset = _UNSET,
        active_project_name: str | _Unset | None = _UNSET,
        ready: bool | _Unset = _UNSET,
    ) -> ShellStatus:
        current = self.status
        status = ShellStatus(
            connectivity=(
                current.connectivity if isinstance(connectivity, _Unset) else connectivity
            ),
            privacy_mode=(
                current.privacy_mode if isinstance(privacy_mode, _Unset) else privacy_mode
            ),
            active_project_name=(
                current.active_project_name
                if isinstance(active_project_name, _Unset)
                else active_project_name
            ),
            ready=current.ready if isinstance(ready, _Unset) else ready,
        )
        self.replace(status)
        return status

    def subscribe(
        self, listener: StatusListener, *, emit_current: bool = False
    ) -> Callable[[], None]:
        with self._lock:
            if listener not in self._listeners:
                self._listeners.append(listener)
            current = self._status
        if emit_current:
            listener(current)

        def unsubscribe() -> None:
            with self._lock:
                if listener in self._listeners:
                    self._listeners.remove(listener)

        return unsubscribe
