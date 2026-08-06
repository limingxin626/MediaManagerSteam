"""Debounced watchdog integration for repository catalog refreshes."""
import logging
import os
import threading

from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer

from app.config import config
from app.services import repository_catalog

logger = logging.getLogger(__name__)
_DEBOUNCE_SECONDS = 1.0
_SUPERVISOR_INTERVAL = 5.0
_observer: Observer | None = None
_handlers: dict[str, "_RepositoryEventHandler"] = {}
_watches = {}
_supervisor: threading.Thread | None = None
_stop = threading.Event()
_guard = threading.Lock()


class _RepositoryEventHandler(FileSystemEventHandler):
    def __init__(self, repo_id: str):
        self.repo_id = repo_id
        self._timer: threading.Timer | None = None
        self._lock = threading.Lock()

    def on_any_event(self, event):
        self.schedule_scan()

    def schedule_scan(self, delay: float = _DEBOUNCE_SECONDS):
        with self._lock:
            if self._timer is not None:
                self._timer.cancel()
            self._timer = threading.Timer(delay, self._scan)
            self._timer.daemon = True
            self._timer.start()

    def _scan(self):
        with self._lock:
            self._timer = None
        if _stop.is_set():
            return
        try:
            result = repository_catalog.rescan(self.repo_id)
            if result is None:
                self.schedule_scan()
        except Exception:
            logger.exception("[catalog-watcher] scan failed for %s", self.repo_id)

    def cancel(self):
        with self._lock:
            if self._timer is not None:
                self._timer.cancel()
                self._timer = None


def _sync_watches() -> None:
    observer = _observer
    if observer is None:
        return
    repos = config.get_repositories()
    with _guard:
        for repo_id, root in repos.items():
            online = os.path.isdir(root)
            if online and repo_id not in _handlers:
                handler = _RepositoryEventHandler(repo_id)
                watch = observer.schedule(handler, root, recursive=True)
                _handlers[repo_id] = handler
                _watches[repo_id] = watch
                handler.schedule_scan(delay=0)
                logger.info("[catalog-watcher] repository %s online; watch attached", repo_id)
            elif not online and repo_id in _handlers:
                handler = _handlers.pop(repo_id)
                watch = _watches.pop(repo_id)
                handler.cancel()
                observer.unschedule(watch)
                logger.warning("[catalog-watcher] repository %s offline; catalog preserved", repo_id)


def _supervise() -> None:
    while not _stop.is_set():
        try:
            _sync_watches()
        except Exception:
            logger.exception("[catalog-watcher] failed to refresh repository watches")
        _stop.wait(_SUPERVISOR_INTERVAL)


def start_watcher() -> None:
    global _observer, _supervisor
    with _guard:
        if _observer is not None:
            return
        _stop.clear()
        observer = Observer()
        observer.start()
        _observer = observer
        _supervisor = threading.Thread(target=_supervise, name="catalog-watch-supervisor", daemon=True)
        _supervisor.start()
    logger.info("[catalog-watcher] supervisor started")


def stop_watcher() -> None:
    global _observer, _supervisor
    _stop.set()
    with _guard:
        observer, supervisor = _observer, _supervisor
        handlers = list(_handlers.values())
        _observer, _supervisor = None, None
        _handlers.clear()
        _watches.clear()
    for handler in handlers:
        handler.cancel()
    if supervisor is not None:
        supervisor.join(timeout=10)
    if observer is not None:
        observer.stop()
        observer.join(timeout=10)
    logger.info("[catalog-watcher] stopped")
