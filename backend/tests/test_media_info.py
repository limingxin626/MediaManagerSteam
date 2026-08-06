from datetime import datetime

from app.utils import MediaInfoUtils


def test_video_hdr_transfer_is_extracted(monkeypatch):
    monkeypatch.setattr(MediaInfoUtils, "_parse_ffprobe", staticmethod(lambda *_: {
        "streams": [{
            "codec_type": "video", "width": 3840, "height": 2160,
            "codec_name": "hevc", "color_transfer": "arib-std-b67",
            "r_frame_rate": "30000/1001",
        }],
        "format": {},
    }))

    info = MediaInfoUtils.get_media_info("movie.mp4", "VIDEO", "ffprobe")

    assert info["is_hdr"] == 1
    assert info["color_transfer"] == "arib-std-b67"


def test_video_epoch_taken_at_is_cleaned(monkeypatch):
    monkeypatch.setattr(MediaInfoUtils, "_parse_ffprobe", staticmethod(lambda *_: {
        "streams": [],
        "format": {"tags": {"creation_time": "1970-01-01T12:34:56Z"}},
    }))
    assert MediaInfoUtils.get_media_info("movie.mp4", "VIDEO", "ffprobe")["taken_at"] is None


def test_video_adjacent_date_is_preserved(monkeypatch):
    monkeypatch.setattr(MediaInfoUtils, "_parse_ffprobe", staticmethod(lambda *_: {
        "streams": [],
        "format": {"tags": {"creation_time": "1970-01-02T00:00:00Z"}},
    }))
    assert MediaInfoUtils.get_media_info("movie.mp4", "VIDEO", "ffprobe")["taken_at"] == datetime(1970, 1, 2)


def test_image_epoch_taken_at_is_cleaned(monkeypatch, tmp_path):
    from PIL import Image

    path = tmp_path / "image.jpg"
    Image.new("RGB", (1, 1)).save(path)
    monkeypatch.setattr(MediaInfoUtils, "_extract_exif_date", staticmethod(lambda _: datetime(1970, 1, 1, 8)))
    assert MediaInfoUtils.get_media_info(str(path), "IMAGE")["taken_at"] is None
