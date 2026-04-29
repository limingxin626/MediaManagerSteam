import os
import logging
import mimetypes
import shutil
import subprocess
import tempfile
import time
from typing import Optional, Dict, Any
from sqlalchemy.orm import Session
from app.models import Media, MessageMedia, media_tag
from app.utils import calculate_file_hash, ThumbnailUtils, MediaInfoUtils
from app.config import config

logger = logging.getLogger(__name__)


def process_standalone_file(
    db: Session,
    file_path: str,
    media_id: Optional[int] = None,
    skip_dedup: bool = False,
) -> Optional[Dict[str, Any]]:
    """
    处理单个文件落地为 Media 行（不创建 MessageMedia 链接）。
    - 计算 hash、提取媒体信息、生成缩略图、`db.flush()`。
    - skip_dedup=True 时强制创建新行（用于预览图独占语义）。
    返回 {"media": Media, "is_new": bool} 或 None（文件不存在或不支持的类型）。
    """
    if not os.path.exists(file_path):
        return None

    media_type = config.get_media_type(file_path)
    if media_type is None:
        logger.warning(f"Unsupported media type, skipping: {file_path}")
        return None

    file_hash = calculate_file_hash(file_path)
    if file_hash is None:
        logger.error(f"Failed to calculate hash, skipping: {file_path}")
        return None

    if not skip_dedup:
        existing_media = db.query(Media).filter(Media.file_hash == file_hash).first()
        if existing_media:
            return {"media": existing_media, "is_new": False}

    if not config.is_mounted_path(file_path):
        ext = os.path.splitext(file_path)[1]
        upload_dir = config.get_upload_dir()
        os.makedirs(upload_dir, exist_ok=True)
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        dest_path = os.path.join(upload_dir, f"{timestamp}{ext}")
        counter = 1
        while os.path.exists(dest_path):
            dest_path = os.path.join(upload_dir, f"{timestamp}_{counter}{ext}")
            counter += 1
        shutil.copy2(file_path, dest_path)
        logger.info(f"Copied non-mounted file to uploads: {file_path} -> {dest_path}")
        file_path = dest_path

    file_size = os.path.getsize(file_path)
    mime_type, _ = mimetypes.guess_type(file_path)
    media_info = MediaInfoUtils.get_media_info(file_path, media_type, config.FFPROBE_PATH)

    media_kwargs = dict(
        file_path=file_path,
        file_hash=file_hash,
        file_size=file_size,
        mime_type=mime_type or 'application/octet-stream',
        width=media_info["width"],
        height=media_info["height"],
        duration_ms=media_info["duration_ms"],
    )
    if media_id is not None:
        media_kwargs["id"] = media_id
    media = Media(**media_kwargs)
    db.add(media)
    db.flush()

    try:
        thumb_path = config.get_thumbnail_path(media.id)
        ThumbnailUtils.generate_thumbnail(file_path, thumb_path, media_type, config.FFMPEG_PATH)
    except Exception as e:
        logger.error(f"Failed to generate thumbnail: {e}")

    return {"media": media, "is_new": True}


def create_preview_media(db: Session, file_path: str) -> Media:
    """为视频预览图强制创建一条新的 Media 行（不去重）。返回 Media。"""
    result = process_standalone_file(db, file_path, skip_dedup=True)
    if result is None:
        raise ValueError("Failed to process preview file")
    return result["media"]


def process_file(db: Session, file_path: str, message_id: int, position: int, media_id: Optional[int] = None) -> Optional[Dict[str, Any]]:
    """
    处理单个文件并链接到消息：复用 process_standalone_file 后再 _link_media。
    返回 {"media": Media, "is_new": bool} 或 None。
    """
    result = process_standalone_file(db, file_path, media_id=media_id)
    if result is None:
        return None
    _link_media(db, message_id, result["media"].id, position)
    return result


def _merge_media_into(db: Session, src: Media, dst: Media) -> None:
    """将 src 的所有引用迁移到 dst，然后删除 src 行（及其缩略图、文件）。
    调用方需保证 src 与 dst 都不是预览帧（video_media_id 为 None）。
    """
    # 1) MessageMedia: 把 src 的链接迁到 dst；遇到 dst 已在同 message 的链接则丢弃
    src_mms = db.query(MessageMedia).filter(MessageMedia.media_id == src.id).all()
    for mm in src_mms:
        existing = db.query(MessageMedia).filter(
            MessageMedia.message_id == mm.message_id,
            MessageMedia.media_id == dst.id,
        ).first()
        if existing is not None:
            db.delete(mm)
        else:
            mm.media_id = dst.id
    db.flush()

    # 2) media_tag: 迁移 tag 关联，跳过重复
    src_tag_rows = db.execute(
        media_tag.select().where(media_tag.c.media_id == src.id)
    ).fetchall()
    dst_tag_ids = {
        r.tag_id for r in db.execute(
            media_tag.select().where(media_tag.c.media_id == dst.id)
        ).fetchall()
    }
    for row in src_tag_rows:
        if row.tag_id not in dst_tag_ids:
            db.execute(media_tag.insert().values(media_id=dst.id, tag_id=row.tag_id))
    db.execute(media_tag.delete().where(media_tag.c.media_id == src.id))

    # 3) 预览帧：src 的 previews 重指向 dst（仅当 dst 是视频时）；否则连同文件/缩略图删除
    preview_rows = db.query(Media).filter(Media.video_media_id == src.id).all()
    if preview_rows:
        if (dst.mime_type or "").startswith("video/"):
            for p in preview_rows:
                p.video_media_id = dst.id
        else:
            for p in preview_rows:
                p_path = p.file_path
                p_id = p.id
                db.execute(media_tag.delete().where(media_tag.c.media_id == p_id))
                db.query(MessageMedia).filter(MessageMedia.media_id == p_id).delete()
                db.delete(p)
                thumb = config.get_thumbnail_path(p_id)
                if os.path.exists(thumb):
                    try: os.remove(thumb)
                    except Exception: pass
                if p_path and os.path.exists(p_path):
                    try: os.remove(p_path)
                    except Exception: pass
    db.flush()

    # 4) 删除 src 的缩略图与文件
    src_id = src.id
    src_path = src.file_path
    db.delete(src)
    db.flush()

    thumb = config.get_thumbnail_path(src_id)
    if os.path.exists(thumb):
        try: os.remove(thumb)
        except Exception as e: logger.warning(f"Failed to remove old thumb {thumb}: {e}")
    if src_path and os.path.exists(src_path):
        try: os.remove(src_path)
        except Exception as e: logger.warning(f"Failed to remove old file {src_path}: {e}")


def replace_media_file(db: Session, media_id: int, src_path: str) -> Media:
    """用 src_path 的文件覆盖 media 当前的文件，保留 Media 行 id。
    - 若新文件的 hash 与另一条 Media 重复，则将当前 media 的引用迁移到那条 Media 并删除当前行，返回那条 Media。
    - 否则原地覆盖：扩展名相同直接覆盖原 file_path，否则改写为新扩展名并删除旧文件。
    - 重新计算 hash/size/mime/分辨率/时长，重生成缩略图
    """
    media = db.query(Media).filter(Media.id == media_id).first()
    if not media:
        raise ValueError("Media not found")
    if media.video_media_id is not None:
        raise ValueError("Cannot replace a video preview frame via this endpoint")

    media_type = config.get_media_type(src_path)
    if media_type is None:
        raise ValueError("Unsupported media type")

    new_hash = calculate_file_hash(src_path)
    if new_hash is None:
        raise RuntimeError("Failed to calculate hash for new file")

    # 去重：若新内容已存在为另一条 Media，则合并
    if new_hash != media.file_hash:
        dup = db.query(Media).filter(
            Media.file_hash == new_hash,
            Media.id != media.id,
        ).first()
        if dup is not None:
            if dup.video_media_id is not None:
                raise ValueError("Replacement matches an existing preview frame; refusing to merge")
            _merge_media_into(db, media, dup)
            db.commit()
            db.refresh(dup)
            return dup

    old_path = media.file_path
    old_ext = os.path.splitext(old_path)[1].lower()
    new_ext = os.path.splitext(src_path)[1].lower()

    if new_ext == old_ext:
        target_path = old_path
        os.makedirs(os.path.dirname(target_path), exist_ok=True)
        shutil.copy2(src_path, target_path)
    else:
        target_path = os.path.splitext(old_path)[0] + new_ext
        os.makedirs(os.path.dirname(target_path), exist_ok=True)
        shutil.copy2(src_path, target_path)
        if old_path != target_path and os.path.exists(old_path):
            try:
                os.remove(old_path)
            except Exception as e:
                logger.warning(f"Failed to remove old file {old_path}: {e}")
        media.file_path = target_path

    media_info = MediaInfoUtils.get_media_info(target_path, media_type, config.FFPROBE_PATH)
    media.file_hash = new_hash
    media.file_size = os.path.getsize(target_path)
    media.mime_type = mimetypes.guess_type(target_path)[0] or 'application/octet-stream'
    media.width = media_info["width"]
    media.height = media_info["height"]
    media.duration_ms = media_info["duration_ms"]

    try:
        thumb_path = config.get_thumbnail_path(media.id)
        ThumbnailUtils.generate_thumbnail(target_path, thumb_path, media_type, config.FFMPEG_PATH)
    except Exception as e:
        logger.error(f"Failed to regenerate thumbnail after replace: {e}")

    db.commit()
    db.refresh(media)
    return media


def rotate_media(db: Session, media_id: int, degrees: int) -> Media:
    media = db.query(Media).filter(Media.id == media_id).first()
    if not media:
        raise ValueError("Media not found")

    file_path = media.file_path
    if not os.path.exists(file_path):
        raise ValueError("Source file not found")

    media_type = config.get_media_type(file_path)
    if media_type == "IMAGE":
        _rotate_image(file_path, degrees)
    elif media_type == "VIDEO":
        _rotate_video(file_path, degrees)
    else:
        raise ValueError("Unsupported media type for rotation")

    if degrees in (90, 270):
        media.width, media.height = media.height, media.width

    media.file_hash = calculate_file_hash(file_path)
    media.file_size = os.path.getsize(file_path)

    thumb_path = config.get_thumbnail_path(media.id)
    try:
        ThumbnailUtils.generate_thumbnail(file_path, thumb_path, media_type, config.FFMPEG_PATH)
    except Exception as e:
        logger.error(f"Failed to regenerate thumbnail after rotation: {e}")

    db.commit()
    return media


def _rotate_image(file_path: str, degrees: int) -> None:
    from PIL import Image, ImageOps

    with Image.open(file_path) as img:
        img = ImageOps.exif_transpose(img)
        img = img.rotate(-degrees, expand=True)

        original_format = img.format or file_path.rsplit('.', 1)[-1].upper()
        ext = os.path.splitext(file_path)[1].lower()
        save_kwargs: dict = {}
        if ext in ('.jpg', '.jpeg'):
            original_format = 'JPEG'
            save_kwargs['quality'] = 95
        elif ext == '.png':
            original_format = 'PNG'

        img.save(file_path, original_format, **save_kwargs)


def _rotate_video(file_path: str, degrees: int) -> None:
    transpose_map = {90: 'transpose=1', 180: 'transpose=1,transpose=1', 270: 'transpose=2'}
    vf = transpose_map[degrees]

    fd, tmp_path = tempfile.mkstemp(suffix=os.path.splitext(file_path)[1])
    os.close(fd)
    try:
        cmd = [
            config.FFMPEG_PATH,
            '-i', file_path,
            '-vf', vf,
            '-c:a', 'copy',
            '-y', tmp_path
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=300,
                                encoding='utf-8', errors='ignore')
        if result.returncode != 0:
            raise RuntimeError(f"ffmpeg rotation failed: {result.stderr[:500]}")
        shutil.move(tmp_path, file_path)
    except Exception:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)
        raise


def _link_media(db: Session, message_id: int, media_id: int, position: int) -> None:
    mm = MessageMedia(message_id=message_id, media_id=media_id, position=position)
    db.add(mm)
