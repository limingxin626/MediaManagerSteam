from datetime import datetime
from types import SimpleNamespace

from app.utils import media_dates


def test_clean_taken_at_discards_epoch_day_only():
    assert media_dates.clean_taken_at(datetime(1970, 1, 1, 23, 59, 59)) is None
    before = datetime(1969, 12, 31, 23, 59, 59)
    after = datetime(1970, 1, 2)
    assert media_dates.clean_taken_at(before) is before
    assert media_dates.clean_taken_at(after) is after


def test_windows_uses_ctime(monkeypatch):
    monkeypatch.setattr(media_dates.os, "stat", lambda _: SimpleNamespace(st_ctime=1234))
    assert media_dates.get_file_created_at("x", platform="win32") == datetime.fromtimestamp(1234)


def test_macos_uses_birthtime(monkeypatch):
    monkeypatch.setattr(
        media_dates.os,
        "stat",
        lambda _: SimpleNamespace(st_ctime=9999, st_birthtime=2345),
    )
    assert media_dates.get_file_created_at("x", platform="darwin") == datetime.fromtimestamp(2345)


def test_unsupported_platform_does_not_use_ctime(monkeypatch):
    monkeypatch.setattr(media_dates.os, "stat", lambda _: SimpleNamespace(st_ctime=1234))
    assert media_dates.get_file_created_at("x", platform="linux") is None


def test_missing_file_returns_none(monkeypatch):
    def missing(_):
        raise FileNotFoundError

    monkeypatch.setattr(media_dates.os, "stat", missing)
    assert media_dates.get_file_created_at("missing", platform="win32") is None
