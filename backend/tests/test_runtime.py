import threading

from app.runtime import BackgroundServiceManager
from app.modules.repository import catalog as repository_catalog
from app.modules.repository import materializer as repository_materializer
from app.modules.repository import watcher as repository_watcher


def test_disabled_background_manager_is_inert():
    manager = BackgroundServiceManager(enabled=False)
    manager.start()
    manager.stop()
    assert manager.started is False


def test_background_manager_start_and_stop_are_idempotent(monkeypatch):
    calls = []
    scanned = threading.Event()
    monkeypatch.setattr(repository_materializer, "start_worker", lambda **_kwargs: calls.append("worker+"))
    monkeypatch.setattr(repository_materializer, "stop_worker", lambda: calls.append("worker-"))
    monkeypatch.setattr(repository_watcher, "start_watcher", lambda **_kwargs: calls.append("watcher+"))
    monkeypatch.setattr(repository_watcher, "stop_watcher", lambda: calls.append("watcher-"))
    monkeypatch.setattr(repository_catalog, "rescan", lambda **_kwargs: scanned.set())

    manager = BackgroundServiceManager()
    manager.start()
    manager.start()
    assert scanned.wait(timeout=2)
    assert manager.started is True
    manager.stop()
    manager.stop()

    assert calls == ["worker+", "watcher+", "watcher-", "worker-"]
    assert manager.started is False


def test_background_manager_isolates_service_failures(monkeypatch):
    calls = []
    monkeypatch.setattr(repository_materializer, "start_worker", lambda **_kwargs: calls.append("worker+"))
    monkeypatch.setattr(repository_watcher, "start_watcher", lambda **_kwargs: (_ for _ in ()).throw(RuntimeError("offline")))
    monkeypatch.setattr(repository_catalog, "rescan", lambda **_kwargs: None)
    monkeypatch.setattr(repository_watcher, "stop_watcher", lambda: calls.append("watcher-"))
    monkeypatch.setattr(repository_materializer, "stop_worker", lambda: calls.append("worker-"))

    manager = BackgroundServiceManager()
    manager.start()
    assert manager.started is True
    manager.stop()
    assert calls == ["worker+", "worker-"]
