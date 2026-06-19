import os
import logging
import mimetypes
import shutil
import subprocess
import tempfile
import time
from typing import Any, BinaryIO, Optional, Dict
from sqlalchemy import func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from app.models import Media, MessageMedia, media_tag
from app.utils import calculate_file_hash, ThumbnailUtils, MediaInfoUtils
from app.config import config

logger = logging.getLogger(__name__)

# 视频 cover sidecar 通用约定:视频文件旁边的同名 `<stem>.cover.{ext}` 文件
# 会被识别为缩略图来源,优先于 ffmpeg 抽帧。匹配 case-insensitive,所以
# 任何下载器(BBDown/yt-dlp/...)生成的 `.cover.jpg` / `.Cover.JPG` 等都命中。
# 这是后端的通用接口,任何批量导入场景只需把 cover 放在视频旁边即可。
_COVER_SIDECAR_EXTS = (".jpg", ".jpeg", ".png", ".webp")


def _find_video_cover_sidecar(video_path: str) -> Optional[str]:
    """查同目录是否有同名 .cover.{ext} sidecar(case-insensitive)。

    例:`/x/foo.mp4` → `/x/foo.cover.jpg`、`/x/foo.Cover.PNG` 均命中。
    返回找到的绝对路径或 None;目录无法列出时返回 None。
    """
    folder, name = os.path.split(video_path)
    stem = os.path.splitext(name)[0]
    needle = (stem + ".cover").lower()
    try:
        entries = os.listdir(folder)
    except OSError:
        return None
    for entry in entries:
        entry_stem, entry_ext = os.path.splitext(entry)
        if entry_stem.lower() == needle and entry_ext.lower() in _COVER_SIDECAR_EXTS:
            return os.path.join(folder, entry)
    return None


def process_file(
    db: Session,
    file_path: str,
    media_id: Optional[int] = None,
    skip_dedup: bool = False,
    commit: bool = True,
) -> Optional[Dict[str, Any]]:
    """
    处理单个文件落地为 Media 行(不创建 MessageMedia 链接)。
    - 计算 hash、提取媒体信息、生成缩略图、`db.flush()`。
    - 视频 sidecar 约定:同目录的 `<stem>.cover.{jpg,jpeg,png,webp}`
      (case-insensitive)会被用作缩略图来源,优先于 ffmpeg 抽帧。
    - skip_dedup=True 时强制创建新行(用于预览图独占语义)。
    - commit=True (默认) 时函数末尾 commit + refresh;False 时由调用者控制事务边界。
    返回 {"media": Media, "is_new": bool} 或 None(文件不存在或不支持的类型)。
    dedup 命中时不 commit(没改 DB)。

    关联到 message 的职责属于 message 域,见
    `app.services.message_service.link_media_to_message`。
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

    # 在拷贝前记下原始路径 —— cover sidecar 只能在原始目录找(uploads/ 里没拷贝)。
    original_file_path = file_path

    # 若 file_path 已落在某个 repo 下,直接登记;否则 copy 进 default repo 的日期目录。
    try:
        repo_id, rel_path = config.register_relative(file_path)
    except ValueError:
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
        logger.info(f"Copied non-repo file to default repo: {file_path} -> {dest_path}")
        file_path = dest_path
        repo_id, rel_path = config.register_relative(file_path)

    file_size = os.path.getsize(file_path)
    mime_type, _ = mimetypes.guess_type(file_path)
    media_info = MediaInfoUtils.get_media_info(file_path, media_type, config.FFPROBE_PATH)

    media_kwargs = dict(
        file_path=rel_path,
        repo_id=repo_id,
        file_hash=file_hash,
        file_size=file_size,
        mime_type=mime_type or 'application/octet-stream',
        width=media_info["width"],
        height=media_info["height"],
        duration_ms=media_info["duration_ms"],
        taken_at=media_info.get("taken_at"),
        gps_lat=media_info.get("gps_lat"),
        gps_lng=media_info.get("gps_lng"),
        orientation=media_info.get("orientation"),
        camera_make=media_info.get("camera_make"),
        camera_model=media_info.get("camera_model"),
        lens=media_info.get("lens"),
        video_codec=media_info.get("video_codec"),
        audio_codec=media_info.get("audio_codec"),
        has_audio=media_info.get("has_audio"),
        fps=media_info.get("fps"),
        bitrate=media_info.get("bitrate"),
    )
    if media_id is not None:
        media_kwargs["id"] = media_id
    media = Media(**media_kwargs)
    db.add(media)
    try:
        db.flush()
    except IntegrityError:
        # 并发上传同一文件时,另一事务已先插入同 file_hash 行 —— 回退使用已存在的那条。
        db.rollback()
        if skip_dedup:
            raise
        existing_media = db.query(Media).filter(Media.file_hash == file_hash).first()
        if existing_media:
            logger.info(f"Race on file_hash {file_hash[:12]}, returning existing media id={existing_media.id}")
            return {"media": existing_media, "is_new": False}
        raise

    try:
        thumb_path = config.get_thumbnail_path(media.id)
        sidecar = _find_video_cover_sidecar(original_file_path) if media_type == "VIDEO" else None
        if sidecar:
            ok = ThumbnailUtils.generate_image_thumbnail(sidecar, thumb_path)
            if ok:
                logger.info(f"Used cover sidecar for media id={media.id}: {sidecar}")
            else:
                logger.warning(f"Cover sidecar failed, falling back to ffmpeg: {sidecar}")
                ThumbnailUtils.generate_thumbnail(file_path, thumb_path, media_type, config.FFMPEG_PATH)
        else:
            ThumbnailUtils.generate_thumbnail(file_path, thumb_path, media_type, config.FFMPEG_PATH)
    except Exception as e:
        logger.error(f"Failed to generate thumbnail for media id={media.id} path={file_path}: {e}")

    if commit:
        db.commit()
        db.refresh(media)
    return {"media": media, "is_new": True}


def create_preview_media(db: Session, file_path: str, commit: bool = True) -> Media:
    """为视频预览图强制创建一条新的 Media 行(不去重)。返回 Media。
    commit 参数透传给 process_file。"""
    result = process_file(db, file_path, skip_dedup=True, commit=commit)
    if result is None:
        raise ValueError("Failed to process preview file")
    return result["media"]


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
                p_abs = config.resolve_to_absolute(p.repo_id, p.file_path)
                p_id = p.id
                db.execute(media_tag.delete().where(media_tag.c.media_id == p_id))
                db.query(MessageMedia).filter(MessageMedia.media_id == p_id).delete()
                db.delete(p)
                thumb = config.get_thumbnail_path(p_id)
                if os.path.exists(thumb):
                    try: os.remove(thumb)
                    except Exception: pass
                if p_abs and os.path.exists(p_abs):
                    try: os.remove(p_abs)
                    except Exception: pass
    db.flush()

    # 4) 删除 src 的缩略图与文件
    src_id = src.id
    src_abs = config.resolve_to_absolute(src.repo_id, src.file_path)
    db.delete(src)
    db.flush()

    thumb = config.get_thumbnail_path(src_id)
    if os.path.exists(thumb):
        try: os.remove(thumb)
        except Exception as e: logger.warning(f"Failed to remove old thumb {thumb}: {e}")
    if src_abs and os.path.exists(src_abs):
        try: os.remove(src_abs)
        except Exception as e: logger.warning(f"Failed to remove old file {src_abs}: {e}")


def replace_media_file(db: Session, media_id: int, src_path: str, commit: bool = True) -> Media:
    """用 src_path 的文件覆盖 media 当前的文件，保留 Media 行 id。
    - 若新文件的 hash 与另一条 Media 重复，则将当前 media 的引用迁移到那条 Media 并删除当前行，返回那条 Media。
    - 否则原地覆盖：扩展名相同直接覆盖原 file_path，否则改写为新扩展名并删除旧文件。
    - 重新计算 hash/size/mime/分辨率/时长，重生成缩略图
    - commit=True (默认) 时函数末尾 commit + refresh;False 时由调用者控制事务边界。
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
            if commit:
                db.commit()
                db.refresh(dup)
            return dup

    old_abs = config.resolve_to_absolute(media.repo_id, media.file_path)
    if old_abs is None:
        raise ValueError(f"Unknown repo {media.repo_id} for media id={media.id}")
    old_ext = os.path.splitext(old_abs)[1].lower()
    new_ext = os.path.splitext(src_path)[1].lower()

    if new_ext == old_ext:
        target_abs = old_abs
        os.makedirs(os.path.dirname(target_abs), exist_ok=True)
        shutil.copy2(src_path, target_abs)
    else:
        target_abs = os.path.splitext(old_abs)[0] + new_ext
        os.makedirs(os.path.dirname(target_abs), exist_ok=True)
        shutil.copy2(src_path, target_abs)
        if old_abs != target_abs and os.path.exists(old_abs):
            try:
                os.remove(old_abs)
            except Exception as e:
                logger.warning(f"Failed to remove old file {old_abs}: {e}")
        new_repo_id, new_rel = config.register_relative(target_abs)
        assert new_repo_id == media.repo_id, (
            f"repo_id changed during replace: {media.repo_id} -> {new_repo_id}"
        )
        media.file_path = new_rel

    media_info = MediaInfoUtils.get_media_info(target_abs, media_type, config.FFPROBE_PATH)
    media.file_hash = new_hash
    media.file_size = os.path.getsize(target_abs)
    media.mime_type = mimetypes.guess_type(target_abs)[0] or 'application/octet-stream'
    media.width = media_info["width"]
    media.height = media_info["height"]
    media.duration_ms = media_info["duration_ms"]
    media.taken_at = media_info.get("taken_at")
    media.gps_lat = media_info.get("gps_lat")
    media.gps_lng = media_info.get("gps_lng")
    media.orientation = media_info.get("orientation")
    media.camera_make = media_info.get("camera_make")
    media.camera_model = media_info.get("camera_model")
    media.lens = media_info.get("lens")
    media.video_codec = media_info.get("video_codec")
    media.audio_codec = media_info.get("audio_codec")
    media.has_audio = media_info.get("has_audio")
    media.fps = media_info.get("fps")
    media.bitrate = media_info.get("bitrate")

    try:
        thumb_path = config.get_thumbnail_path(media.id)
        ThumbnailUtils.generate_thumbnail(target_abs, thumb_path, media_type, config.FFMPEG_PATH)
    except Exception as e:
        logger.error(f"Failed to regenerate thumbnail after replace: {e}")

    if commit:
        db.commit()
        db.refresh(media)
    return media


def rotate_media(db: Session, media_id: int, degrees: int, commit: bool = True) -> Media:
    media = db.query(Media).filter(Media.id == media_id).first()
    if not media:
        raise ValueError("Media not found")

    file_path = config.resolve_to_absolute(media.repo_id, media.file_path)
    if file_path is None or not os.path.exists(file_path):
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

    if commit:
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


# ----------------------------------------------------------------------------
# Preview attach / delete (Group 4)
# ----------------------------------------------------------------------------

def _require_video_for_preview(db: Session, video_media_id: int) -> Media:
    """校验 video_media_id 存在且是 video。返回 Media,否则 raise ValueError。"""
    media = db.query(Media).filter(Media.id == video_media_id).first()
    if not media:
        raise ValueError(f"Media {video_media_id} not found")
    if not (media.mime_type or "").startswith("video/"):
        raise ValueError(f"Media {video_media_id} is not a video")
    return media


def _validate_preview_range(frame_ms: int, start_ms: Optional[int], end_ms: Optional[int]) -> None:
    """校验 frame_ms / start_ms / end_ms 的语义。"""
    if frame_ms < 0:
        raise ValueError("frame_ms must be >= 0")
    if start_ms is not None and start_ms < 0:
        raise ValueError("start_ms must be >= 0")
    if end_ms is not None and end_ms < 0:
        raise ValueError("end_ms must be >= 0")
    if start_ms is not None and end_ms is not None and end_ms < start_ms:
        raise ValueError("end_ms must be >= start_ms")


def attach_existing_preview(
    db: Session,
    video_media_id: int,
    preview_media_id: int,
    frame_ms: int,
    start_ms: Optional[int] = None,
    end_ms: Optional[int] = None,
    commit: bool = True,
) -> Media:
    """把一张已存在的 image 挂到 video 下作为 preview/chapter。

    业务校验:preview_media_id 必须是 image、不能已被其它 video 用过、
    不能等于 video_media_id 自身。

    Raises:
        ValueError: 校验失败(语义见 HTTP 状态码映射)
    """
    if preview_media_id == video_media_id:
        raise ValueError("preview_media_id cannot equal video media id")
    _require_video_for_preview(db, video_media_id)
    _validate_preview_range(frame_ms, start_ms, end_ms)

    image = db.query(Media).filter(Media.id == preview_media_id).first()
    if not image:
        raise ValueError("Preview media not found")
    if not (image.mime_type or "").startswith("image/"):
        raise ValueError("Preview media must be an image")
    if image.video_media_id is not None:
        raise ValueError("Preview media is already used by another video")

    image.video_media_id = video_media_id
    image.frame_ms = frame_ms
    image.start_ms = start_ms
    image.end_ms = end_ms

    if commit:
        db.commit()
        db.refresh(image)
    return image


def attach_screenshot_preview(
    db: Session,
    video_media_id: int,
    file_obj: BinaryIO,
    filename: str,
    content_type: str,
    frame_ms: int,
    start_ms: Optional[int] = None,
    end_ms: Optional[int] = None,
    commit: bool = True,
) -> Media:
    """从上传的截图创建 preview。

    关键修复(相对旧 router):文件先写到 `*.tmp` 中间路径,所有 DB 操作成功后才
    `os.rename` 到最终路径;任意步骤 raise 都会在 `finally` 清理 tmp。
    这避免"DB 回滚但文件已落盘"的孤儿。

    Raises:
        ValueError: 业务校验失败
    """
    if not (content_type or "").startswith("image/"):
        raise ValueError("Uploaded file must be an image")
    _validate_preview_range(frame_ms, start_ms, end_ms)
    _require_video_for_preview(db, video_media_id)

    upload_dir = config.get_upload_dir()
    os.makedirs(upload_dir, exist_ok=True)
    ext = os.path.splitext(filename or "")[1].lower() or ".jpg"
    if ext not in (".jpg", ".jpeg", ".png", ".webp"):
        ext = ".jpg"
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    base = f"preview_{video_media_id}_{timestamp}{ext}"
    dest_path = os.path.join(upload_dir, base)
    counter = 1
    while os.path.exists(dest_path):
        dest_path = os.path.join(upload_dir, f"preview_{video_media_id}_{timestamp}_{counter}{ext}")
        counter += 1
    # tmp 后缀放在扩展名前(如 preview_1_xxx.tmp.png),这样 os.path.splitext 仍能识别 .png
    tmp_path = dest_path[:-len(ext)] + ".tmp" + ext

    try:
        # Step 1: 写到 tmp 路径
        with open(tmp_path, "wb") as f:
            shutil.copyfileobj(file_obj, f, length=1024 * 1024)

        # Step 2: 创建 Media 行(不去重)
        image = create_preview_media(db, tmp_path, commit=False)

        # Step 3: 设 video_media_id + 帧信息
        image.video_media_id = video_media_id
        image.frame_ms = frame_ms
        image.start_ms = start_ms
        image.end_ms = end_ms
        db.flush()

        # Step 4: 挂到最早引用此 video 的 message
        earliest_mm = (
            db.query(MessageMedia)
            .filter(MessageMedia.media_id == video_media_id)
            .order_by(MessageMedia.created_at.asc(), MessageMedia.id.asc())
            .first()
        )
        if earliest_mm is not None:
            target_message_id = earliest_mm.message_id
            max_position = (
                db.query(func.coalesce(func.max(MessageMedia.position), -1))
                .filter(MessageMedia.message_id == target_message_id)
                .scalar()
            )
            db.add(MessageMedia(
                message_id=target_message_id,
                media_id=image.id,
                position=int(max_position) + 1,
            ))

        if commit:
            db.commit()
            db.refresh(image)
        else:
            # commit=False 时,文件先不 rename;caller 决定何时 commit
            return image

        # Step 5: 全部成功,rename tmp → final(commit 后再做,确保 DB 已持久)
        os.rename(tmp_path, dest_path)
        return image

    except Exception:
        if commit:
            # commit 失败(或中途 raise),删除 tmp 文件
            if os.path.exists(tmp_path):
                try: os.remove(tmp_path)
                except Exception: pass
        raise
    finally:
        if not commit:
            # commit=False 模式:tmp 路径已写入,事务结束后 caller 决定
            pass


def delete_media(
    db: Session,
    media_id: int,
    unlink_from_message_id: Optional[int] = None,
    delete_source_file: bool = False,
    commit: bool = True,
) -> Dict[str, Any]:
    """删除一条 media。

    - 若 unlink_from_message_id 提供且该 media 被多条 message 引用,只解除这条关联,
      返回 {"action": "unlinked", "media_id": ...}。
    - 否则全删(级联 MessageMedia + media_tag + 文件 + 缩略图),
      返回 {"action": "deleted", "media_id": ...}。
    - delete_source_file: 仅在"deleted"分支生效,删除磁盘源文件(默认 False,保留文件)。

    Returns:
        {"action": "unlinked" | "deleted", "media_id": int}
        或 None(若 media_id 不存在)

    Raises:
        ValueError: media 不存在
    """
    media = db.query(Media).filter(Media.id == media_id).first()
    if not media:
        raise ValueError("Media not found")

    if unlink_from_message_id is not None:
        ref_count = db.query(MessageMedia).filter(MessageMedia.media_id == media_id).count()
        if ref_count > 1:
            db.query(MessageMedia).filter(
                MessageMedia.media_id == media_id,
                MessageMedia.message_id == unlink_from_message_id,
            ).delete(synchronize_session=False)
            if commit:
                db.commit()
            return {"action": "unlinked", "media_id": media_id}

    file_path = config.resolve_to_absolute(media.repo_id, media.file_path)
    media_id_to_clean = media_id

    db.query(MessageMedia).filter(MessageMedia.media_id == media_id).delete(synchronize_session=False)
    db.execute(media_tag.delete().where(media_tag.c.media_id == media_id))
    db.delete(media)

    if commit:
        db.commit()

    # 文件清理在 commit 之后做(失败不影响 DB 状态)
    thumb_path = config.get_thumbnail_path(media_id_to_clean)
    if os.path.exists(thumb_path):
        try: os.remove(thumb_path)
        except Exception as e: logger.warning(f"Failed to remove thumb {thumb_path}: {e}")

    if delete_source_file and file_path and os.path.exists(file_path):
        try:
            os.remove(file_path)
        except Exception as e:
            logger.warning(f"Failed to remove source file {file_path}: {e}")

    return {"action": "deleted", "media_id": media_id_to_clean}
