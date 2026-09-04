"""Maintain logical folders independently from messages."""
import os
import re
import shutil
import uuid
import xml.etree.ElementTree as ET
from collections import defaultdict
from datetime import datetime
from typing import BinaryIO, Optional, cast

from sqlalchemy.orm import Session

from app.config import config
from app.models import Folder, FolderLocation, Person, RepositoryFile, RepositoryFolder
from app.modules.repository.folder_classifier import FolderClassification, classify_folder


def _primary_location(folder: Folder) -> FolderLocation | None:
    return next((location for location in folder.locations if location.role == "PRIMARY"), None)


def repository_folder_has_nfo(physical: RepositoryFolder) -> bool:
    """该物理目录里是否含 .nfo(影片元数据证据;.nfo 不进 catalog,须读物理目录)。"""
    directory = config.resolve_to_absolute(physical.repo_id, physical.rel_path)
    if directory is None or not os.path.isdir(directory):
        return False
    try:
        return any(name.lower().endswith(".nfo") for name in os.listdir(directory))
    except OSError:
        return False


# Kodi/Emby 风格 .nfo 里携带发行日期的标签(按优先级)。前两个通常是完整日期
# (YYYY-MM-DD,可能带时间),year 只给年份。
_NFO_DATE_TAGS = ("premiered", "release", "aired")
_NFO_YEAR_TAG = "year"
# 解析 "2014-01-01" / "2014-01-01T00:00:00" 这类日期。
_NFO_FULL_DATE_RE = re.compile(r"^\s*(\d{4})-(\d{1,2})-(\d{1,2})")
# .nfo 中作品类型的根节点;只有这些才被当作人物/日期解析来源。
_NFO_WORK_TAGS = ("movie", "tvshow", "episodedetails")


def parse_folder_nfo_release_date(physical: RepositoryFolder) -> Optional[datetime]:
    """从物理目录的 .nfo 里提取发行日期,没有 .nfo 或无可识别日期返回 None。

    仅读取同目录的 .nfo(与影片证据规则一致,不递归)。优先取完整日期
    (premiered/release/aired),取不到再退回 year 年份(默认 1 月 1 日)。
    """
    directory = config.resolve_to_absolute(physical.repo_id, physical.rel_path)
    if directory is None or not os.path.isdir(directory):
        return None
    try:
        entries = os.listdir(directory)
    except OSError:
        return None
    nfo_names = [name for name in entries if name.lower().endswith(".nfo")]
    if not nfo_names:
        return None
    for name in nfo_names:
        path = os.path.join(directory, name)
        try:
            tree = ET.parse(path)
        except (ET.ParseError, OSError):
            continue
        root = tree.getroot()
        # 只认 movie/tvshow 这类作品根节点,避免误读其它 xml。
        tag = _normalized_tag(root.tag)
        if tag not in _NFO_WORK_TAGS:
            continue
        for date_tag in _NFO_DATE_TAGS:
            match = _find_tag_text(root, date_tag)
            if match:
                parsed = _match_full_date(match)
                if parsed is not None:
                    return parsed
        year_text = _find_tag_text(root, _NFO_YEAR_TAG)
        if year_text:
            year = re.match(r"^\s*(\d{4})", year_text)
            if year:
                return datetime(int(year.group(1)), 1, 1)
    return None


def parse_folder_nfo_actors(physical: RepositoryFolder) -> list[str]:
    """从物理目录的 .nfo 提取演员名单(去重保序)。

    仅读取同目录的 .nfo(与影片证据/发行日期规则一致,不递归)。取每个作品
    (movie/tvshow/episodedetails)根节点下 ``<actor><name>…</name></actor>`` 的
    name 文本;兼容个别 nfo 直接把演员名写在 ``<actor>`` 文本里。无 .nfo、
    无可识别演员时返回空列表。
    """
    directory = config.resolve_to_absolute(physical.repo_id, physical.rel_path)
    if directory is None or not os.path.isdir(directory):
        return []
    try:
        entries = os.listdir(directory)
    except OSError:
        return []
    nfo_names = [name for name in entries if name.lower().endswith(".nfo")]
    actors: list[str] = []
    seen: set[str] = set()
    for name in nfo_names:
        path = os.path.join(directory, name)
        try:
            tree = ET.parse(path)
        except (ET.ParseError, OSError):
            continue
        root = tree.getroot()
        if _normalized_tag(root.tag) not in _NFO_WORK_TAGS:
            continue
        for element in root.iter():
            if _normalized_tag(element.tag) != "actor":
                continue
            actor_name = None
            for child in element.iter():
                if _normalized_tag(child.tag) == "name" and (child.text or "").strip():
                    actor_name = child.text.strip()
                    break
            if not actor_name:
                actor_name = (element.text or "").strip()
            if actor_name and actor_name.casefold() not in seen:
                seen.add(actor_name.casefold())
                actors.append(actor_name)
    return actors


def _normalized_tag(tag: str) -> str:
    # ElementTree 的 tag 可能是 "{namespace}movie" 形式。
    return tag.rsplit("}", 1)[-1].strip().lower()


def _find_tag_text(root: ET.Element, tag_name: str) -> Optional[str]:
    """返回 root 下第一个匹配 tag(无论深浅、是否带命名空间)的文本,找不到返回 None。"""
    for element in root.iter():
        if _normalized_tag(element.tag) == tag_name:
            text = (element.text or "").strip()
            if text:
                return text
    return None


def _match_full_date(text: str) -> Optional[datetime]:
    match = _NFO_FULL_DATE_RE.match(text)
    if match is None:
        return None
    year, month, day = (int(group) for group in match.groups())
    try:
        return datetime(year, month, day)
    except ValueError:
        return None


def classify_logical_folder(db: Session, folder: Folder) -> FolderClassification:
    """Run the classifier over a logical folder's catalogued files and return the result.

    The caller decides whether/how to persist ``folder.kind``.
    """
    primary = _primary_location(folder)
    physical = primary.repository_folder if primary is not None else None
    name = physical.name if physical is not None else ""
    physical_ids = [location.repository_folder_id for location in folder.locations]
    files: list[RepositoryFile] = []
    if physical_ids:
        files = db.query(RepositoryFile).filter(RepositoryFile.folder_id.in_(physical_ids)).all()
    primary_folder_id = physical.id if physical is not None else None
    return classify_folder(name, files, primary_folder_id, has_nfo=repository_folder_has_nfo(physical) if physical is not None else False)


def refresh_folder_kind(db: Session, folder: Folder) -> str:
    """Recompute and persist ``folder.kind``; returns the resulting kind string."""
    classification = classify_logical_folder(db, folder)
    folder.kind = classification.kind
    return classification.kind


def refresh_repository_folder_kinds(db: Session, repo_id: str) -> int:
    """Reclassify and persist kind for every logical folder rooted in ``repo_id``.

    Batches file loading (one query per repo, no per-folder N+1). The linkage to
    the logical ``Folder`` is resolved with a SQL join rather than the
    ``RepositoryFolder.folder_location`` relationship attribute, which can hold a
    stale ``None`` right after ``ensure_folders`` creates the link in the same
    session. Returns the number of logical folders refreshed. Caller commits.
    """
    links = (
        db.query(RepositoryFolder, FolderLocation)
        .join(FolderLocation, FolderLocation.repository_folder_id == RepositoryFolder.id)
        .filter(RepositoryFolder.repo_id == repo_id)
        .all()
    )
    by_logical: dict[int, list[tuple[RepositoryFolder, str]]] = defaultdict(list)
    for physical, location in links:
        by_logical[location.folder_id].append((physical, location.role))
    if not by_logical:
        return 0

    physical_ids = [physical.id for items in by_logical.values() for physical, _ in items]
    files_by_physical: dict[int, list[RepositoryFile]] = defaultdict(list)
    for file_row in db.query(RepositoryFile).filter(RepositoryFile.folder_id.in_(physical_ids)):
        files_by_physical[file_row.folder_id].append(file_row)

    refreshed = 0
    for folder_id, members in by_logical.items():
        folder = db.get(Folder, folder_id)
        if folder is None:
            continue
        # Prefer the PRIMARY location (unique per logical folder); else first by id.
        members.sort(key=lambda item: (item[1] != "PRIMARY", item[0].id))
        primary = members[0][0]
        files: list[RepositoryFile] = []
        for physical, _role in members:
            files.extend(files_by_physical.get(physical.id, ()))
        classification = classify_folder(
            primary.name, files, primary.id,
            has_nfo=repository_folder_has_nfo(primary),
        )
        folder.kind = classification.kind
        refreshed += 1
    return refreshed


def refresh_repository_folder_release_dates(db: Session, repo_id: str) -> int:
    """从每个逻辑目录的 .nfo 填充 ``released_at``(仅填尚未设置的空值)。

    入库的 folder 目前不自动抓取元数据;这里的唯一自动来源是随目录落盘的本地
    .nfo。只补 ``released_at IS NULL`` 的行,避免覆盖手动设置的值。返回更新的
    逻辑 folder 数量。调用方 commit。
    """
    links = (
        db.query(RepositoryFolder, FolderLocation)
        .join(FolderLocation, FolderLocation.repository_folder_id == RepositoryFolder.id)
        .filter(RepositoryFolder.repo_id == repo_id)
        .all()
    )
    # 每个逻辑 folder 用 PRIMARY(无则 id 最小)位置作为 .nfo 读取来源。
    by_logical: dict[int, RepositoryFolder] = {}
    for physical, location in links:
        current = by_logical.get(location.folder_id)
        if current is None or (location.role == "PRIMARY" and current.folder_location.role != "PRIMARY"):
            by_logical[location.folder_id] = physical
    if not by_logical:
        return 0

    filled = 0
    for folder_id, physical in by_logical.items():
        folder = db.get(Folder, folder_id)
        if folder is None or folder.released_at is not None:
            continue
        released = parse_folder_nfo_release_date(physical)
        if released is not None:
            folder.released_at = released
            filled += 1
    return filled


def _ensure_persons_by_name(db: Session, names: list[str], cache: dict[str, Person]) -> list[Person]:
    """按名字 get-or-create ``Person`` 行(全局唯一,exact-name 去重)。

    ``cache`` 在同一轮 refresh 里跨 folder 复用,避免对共用演员重复查询/新建。
    返回与 ``names`` 同序的 person 列表。
    """
    missing = [name for name in names if name not in cache]
    if missing:
        existing = {p.name: p for p in db.query(Person).filter(Person.name.in_(missing))}
        for name in missing:
            person = existing.get(name)
            if person is None:
                person = Person(name=name, description=None)
                db.add(person)
                db.flush()  # 分配 id 以便后面赋值关联
            cache[name] = person
    return [cache[name] for name in names]


def refresh_repository_folder_people(db: Session, repo_id: str) -> int:
    """从影片目录的 .nfo 把 ``<actor>`` 自动解析为 ``Person`` 并挂到逻辑 folder。

    只处理 ``kind == "movie"`` 的逻辑 folder —— 与判片规则一致,.nfo 的演员名单
    仅对作品目录有意义。每个逻辑 folder 以 PRIMARY 物理目录为 .nfo 读取来源;
    目录里没有 .nfo 或解析不出任何演员时跳过(不改动既有 people)。

    一旦某目录成功解析出至少一位演员,就以 .nfo 名单为权威**整体替换**
    folder.people(get-or-create 全局去重)。返回更新的逻辑 folder 数量。调用方 commit。
    """
    links = (
        db.query(RepositoryFolder, FolderLocation)
        .join(FolderLocation, FolderLocation.repository_folder_id == RepositoryFolder.id)
        .filter(RepositoryFolder.repo_id == repo_id)
        .all()
    )
    by_logical: dict[int, RepositoryFolder] = {}
    for physical, location in links:
        current = by_logical.get(location.folder_id)
        if current is None or (location.role == "PRIMARY" and current.folder_location.role != "PRIMARY"):
            by_logical[location.folder_id] = physical
    if not by_logical:
        return 0

    updated = 0
    cache: dict[str, Person] = {}
    for folder_id, physical in by_logical.items():
        folder = db.get(Folder, folder_id)
        if folder is None or folder.kind != "movie":
            continue
        actors = parse_folder_nfo_actors(physical)
        if not actors:
            continue
        folder.people = _ensure_persons_by_name(db, actors, cache)
        updated += 1
    return updated


def refresh_kind_for_repository_folder(db: Session, repository_folder_id: int) -> bool:
    """Refresh the kind of the logical folder that owns ``repository_folder_id``.

    Used after a single file materializes so a folder's category stays accurate
    without a full reclassification pass. Returns whether a logical folder changed.
    """
    location = (
        db.query(FolderLocation)
        .filter_by(repository_folder_id=repository_folder_id)
        .first()
    )
    if location is None:
        return False
    folder = db.get(Folder, location.folder_id)
    if folder is None:
        return False
    refresh_folder_kind(db, folder)
    return True


def _has_user_metadata(folder: Folder) -> bool:
    return bool(
        folder.collection_id is not None
        or folder.issue_id is not None
        or folder.starred
        or folder.tags
    )


def ensure_folders(db: Session, repo_id: str) -> set[int]:
    physical_folders = db.query(RepositoryFolder).filter(
        RepositoryFolder.repo_id == repo_id,
        RepositoryFolder.rel_path != "",
    ).all()
    folder_ids: set[int] = set()

    for physical in physical_folders:
        has_files = db.query(RepositoryFile.id).filter_by(folder_id=physical.id).first() is not None
        location = physical.folder_location
        if not has_files:
            if location is not None and not _has_user_metadata(location.folder):
                logical = location.folder
                db.delete(location)
                db.flush()
                if not logical.locations:
                    db.delete(logical)
                else:
                    primary = next((item for item in logical.locations if item.role == "PRIMARY"), None)
                    if primary is None:
                        logical.locations[0].role = "PRIMARY"
            continue

        if location is None:
            logical = Folder(created_at=physical.created_at, updated_at=physical.updated_at)
            db.add(logical)
            db.flush()
            db.add(FolderLocation(
                folder_id=logical.id,
                repository_folder_id=physical.id,
                role="PRIMARY",
            ))
            folder_ids.add(cast(int, logical.id))
        else:
            folder_ids.add(cast(int, location.folder_id))

    db.flush()
    orphaned = db.query(Folder).filter(~Folder.locations.any()).all()
    for logical in orphaned:
        if not _has_user_metadata(logical):
            db.delete(logical)
    db.flush()
    return folder_ids


def store_file_in_primary_folder(
    db: Session,
    folder_id: int,
    filename: str,
    source: BinaryIO,
) -> tuple[str, str]:
    location = db.query(FolderLocation).filter_by(folder_id=folder_id, role="PRIMARY").first()
    if location is None:
        raise ValueError("Folder has no primary repository location")
    if config.get_media_type(filename) is None:
        raise ValueError("Unsupported media file type")

    physical = location.repository_folder
    directory = config.resolve_to_absolute(physical.repo_id, physical.rel_path)
    if directory is None or not os.path.isdir(directory):
        raise FileNotFoundError("Primary repository folder is unavailable")

    safe_name = os.path.basename(filename)
    stem, extension = os.path.splitext(safe_name)
    destination = os.path.join(directory, safe_name)
    counter = 1
    while os.path.exists(destination):
        destination = os.path.join(directory, f"{stem}_{counter}{extension}")
        counter += 1

    temporary = os.path.join(directory, f".{uuid.uuid4().hex}.upload")
    try:
        with open(temporary, "wb") as output:
            shutil.copyfileobj(source, output)
        os.replace(temporary, destination)
    finally:
        if os.path.exists(temporary):
            os.remove(temporary)
    return physical.repo_id, destination
