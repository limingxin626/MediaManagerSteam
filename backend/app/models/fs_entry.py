"""磁盘扫描索引表(`fs_entry`)的 ORM。

与 `Media` 正交的语义:
- `Media` = 已去重(`file_hash` UNIQUE)、已 import 的**逻辑资产库**。
- `FsEntry` = **磁盘物理真相**。同一份内容在两个路径 → 两行(故意不去重);
  唯一约束只有 `(repo_id, rel_path)`(路径唯一,内容可重复)。

填充分两阶段:
1. 扫描期(`scan_service.rescan`)只 `os.stat`,秒级填 repo_id/rel_path/size/mtime/
   media_type/mime/media_id(精确路径匹配 Media)。
2. 后台 worker(`scan_worker`)逐个读文件抽 metadata(分辨率/GPS/相机/HDR/编码…)
   + 生成缩略图,或对匹配到 Media 的行直接从 Media 行搬 metadata(不读文件)。

metadata 列是 `Media` 同名列的镜像(便于 worker 直接 setattr 搬运),外加
`is_hdr` / `color_transfer`(Media 没有的 HDR 信息)。
"""
from datetime import datetime

from sqlalchemy import Column, DateTime, Float, Integer, String, Index, UniqueConstraint

from app.models import Base


class FsEntry(Base):
    __tablename__ = "fs_entry"

    id = Column(Integer, primary_key=True, index=True)

    # ── 扫描期填充(os.stat,无文件读取)──────────────────────────
    repo_id = Column(String(64), nullable=False)
    rel_path = Column(String(1024), nullable=False)       # forward-slash,相对 repo 根
    mime_type = Column(String(100), nullable=True)        # scan_mime_type() 猜测,保证非空 video/* | image/*
    media_type = Column(String(16), nullable=False)       # "VIDEO" | "IMAGE"(grid type 过滤靠它)
    file_size = Column(Integer, nullable=True)            # st_size
    mtime = Column(Float, nullable=False)                 # st_mtime(排序主力)
    scanned_at = Column(DateTime, default=datetime.now, nullable=False)  # mark-and-sweep run token
    created_at = Column(DateTime, default=datetime.now, nullable=False)  # first-seen
    media_id = Column(Integer, nullable=True)             # 精确 (repo_id, file_path) 匹配到的 Media.id;**无 FK**

    # ── 处理状态 ──────────────────────────────────────────────────
    # pending | reused(从 Media 搬 / 指向 Media 缩略图)| done(worker 读文件)| failed
    meta_status = Column(String(16), nullable=False, default="pending", server_default="pending")
    thumb_status = Column(String(16), nullable=False, default="pending", server_default="pending")

    # ── worker / reused 填充(Media 同名列镜像 + HDR)─────────────
    width = Column(Integer, nullable=True)
    height = Column(Integer, nullable=True)
    duration_ms = Column(Integer, nullable=True)
    fps = Column(Float, nullable=True)
    bitrate = Column(Integer, nullable=True)
    video_codec = Column(String(32), nullable=True)
    audio_codec = Column(String(32), nullable=True)
    has_audio = Column(Integer, nullable=True)
    taken_at = Column(DateTime, nullable=True)
    gps_lat = Column(Float, nullable=True)
    gps_lng = Column(Float, nullable=True)
    orientation = Column(Integer, nullable=True)
    camera_make = Column(String(64), nullable=True)
    camera_model = Column(String(64), nullable=True)
    lens = Column(String(128), nullable=True)
    is_hdr = Column(Integer, nullable=True)               # 1 | 0 | NULL(未知)
    color_transfer = Column(String(32), nullable=True)    # e.g. smpte2084 / arib-std-b67

    __table_args__ = (
        # 唯一性只有路径 —— 与 Media.file_hash UNIQUE 的本质差异(不去重)
        UniqueConstraint("repo_id", "rel_path", name="uq_fs_entry_repo_relpath"),
        Index("ix_fs_entry_mtime", "mtime"),
        Index("ix_fs_entry_file_size", "file_size"),
        Index("ix_fs_entry_repo_id", "repo_id"),
        Index("ix_fs_entry_media_id", "media_id"),
        Index("ix_fs_entry_meta_status", "meta_status"),
    )
