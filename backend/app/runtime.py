"""Ownership of process-local background services."""
from __future__ import annotations

import threading
import logging
from typing import Callable

from app.config import AppConfig, get_settings, use_settings

logger = logging.getLogger(__name__)


def _rescan_catalog(settings: AppConfig, session_factory=None) -> None:
    from app.modules.repository import catalog as repository_catalog
    with use_settings(settings):
        try:
            repository_catalog.rescan(session_factory=session_factory)
        except Exception:
            logger.exception("[catalog-bootstrap] initial rescan failed")


class BackgroundServiceManager:
    """Start and stop catalog services as one idempotent lifecycle unit."""

    def __init__(self, *, enabled: bool = True, settings: AppConfig | None = None, session_factory=None) -> None:
        self.enabled = enabled
        self.settings = settings or get_settings()
        self.session_factory = session_factory
        self._started = False
        self._lock = threading.Lock()
        self._bootstrap: threading.Thread | None = None
        self._stoppers: list[tuple[str, Callable[[], None]]] = []

    @property
    def started(self) -> bool:
        return self._started

    def start(self) -> None:
        if not self.enabled:
            return
        with self._lock:
            if self._started:
                return
            from app.modules.repository.materializer import start_worker
            from app.modules.repository.materializer import stop_worker
            from app.modules.repository.watcher import start_watcher, stop_watcher
            for name, starter, stopper in (
                ("materializer", start_worker, stop_worker),
                ("watcher", start_watcher, stop_watcher),
            ):
                try:
                    with use_settings(self.settings):
                        starter(settings=self.settings, session_factory=self.session_factory)
                    self._stoppers.append((name, stopper))
                except Exception:
                    logger.exception("[%s] background service failed to start", name)
            self._bootstrap = threading.Thread(
                target=_rescan_catalog, args=(self.settings, self.session_factory), name="catalog-bootstrap", daemon=True
            )
            self._bootstrap.start()
            self._started = True

    def stop(self) -> None:
        if not self.enabled:
            return
        with self._lock:
            if not self._started:
                return
            for name, stopper in reversed(self._stoppers):
                try:
                    stopper()
                except Exception:
                    logger.exception("[%s] background service failed to stop", name)
            self._stoppers.clear()
            self._started = False
            self._bootstrap = None
