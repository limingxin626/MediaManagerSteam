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
