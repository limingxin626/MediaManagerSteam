from datetime import datetime

from app.models import Media
from scripts import repair_media_dates


def test_repair_dry_run_does_not_write_and_apply_repairs(catalog_env, monkeypatch):
    repo, session_factory = catalog_env
    source = repo / "photo.jpg"
    source.write_bytes(b"image")
    expected_created_at = datetime(2020, 5, 6, 7, 8, 9)
    monkeypatch.setattr(repair_media_dates, "get_file_created_at", lambda _: expected_created_at)

    with session_factory() as db:
        db.add(Media(
            id=1,
            repo_id="test",
            file_path="photo.jpg",
            file_hash="hash",
            file_size=5,
            mime_type="image/jpeg",
            taken_at=datetime(1970, 1, 1, 12),
        ))
        db.commit()

    dry_run = repair_media_dates.repair_media_dates(
        apply=False,
        session_factory=session_factory,
    )
    assert dry_run["epoch_taken_at"] == 1
    assert dry_run["file_created_at"] == 1
    with session_factory() as db:
        media = db.get(Media, 1)
        assert media.taken_at == datetime(1970, 1, 1, 12)
        assert media.file_created_at is None

    applied = repair_media_dates.repair_media_dates(
        apply=True,
        session_factory=session_factory,
    )
    assert applied["epoch_taken_at"] == 1
    assert applied["file_created_at"] == 1
    with session_factory() as db:
        media = db.get(Media, 1)
        assert media.taken_at is None
        assert media.file_created_at == expected_created_at
