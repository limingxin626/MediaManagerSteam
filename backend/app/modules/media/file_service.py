"""File-oriented media use cases used by the HTTP boundary."""
import os
import shutil
import tempfile
import time
from typing import BinaryIO

from app.config import config
from app.models import Media
from app.modules.media.service import replace_media_file
from app.utils import ThumbnailUtils


def replace_from_upload(db, media_id: int, file_obj: BinaryIO, filename: str) -> Media:
    extension = os.path.splitext(filename)[1].lower()
    if config.get_media_type(f"x{extension}") is None:
        raise ValueError("Unsupported media type")
    upload_dir = config.get_upload_dir(); os.makedirs(upload_dir, exist_ok=True)
    stamp = time.strftime("%Y%m%d_%H%M%S"); temp_path = os.path.join(upload_dir, f"replace_{media_id}_{stamp}{extension}")
    counter = 1
    while os.path.exists(temp_path):
        temp_path = os.path.join(upload_dir, f"replace_{media_id}_{stamp}_{counter}{extension}"); counter += 1
    try:
        with open(temp_path, "wb") as output: shutil.copyfileobj(file_obj, output, length=1024 * 1024)
        return replace_media_file(db, media_id, temp_path)
    finally:
        if os.path.exists(temp_path):
            try: os.remove(temp_path)
            except OSError: pass


def set_cover(media: Media, file_obj: BinaryIO, filename: str) -> bool:
    absolute = config.resolve_to_absolute(media.repo_id, media.file_path)
    if not absolute or not os.path.exists(absolute):
        raise FileNotFoundError("Video file not found on disk")
    suffix = os.path.splitext(filename)[1] or ".jpg"; temp_path = None
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as output:
            temp_path = output.name; shutil.copyfileobj(file_obj, output, length=1024 * 1024)
        return ThumbnailUtils.generate_image_thumbnail(temp_path, config.get_thumbnail_path(media.id))
    finally:
        if temp_path:
            try: os.remove(temp_path)
            except OSError: pass
