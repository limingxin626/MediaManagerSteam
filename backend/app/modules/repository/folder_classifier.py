"""Infer the logical contents of a media folder from its catalogued files.

The classifier is deliberately read-only.  Its result can later be overridden by
persisted NFO/manual metadata without changing the Folder detail API shape.
"""
from __future__ import annotations

from dataclasses import dataclass, field
import os
import re
import unicodedata
from typing import Iterable

from app.models import RepositoryFile


ARTWORK_STEMS = {"poster", "fanart", "banner", "clearlogo", "logo", "landscape", "thumb"}
EXTRA_WORDS = {
    "trailer", "sample", "theme", "featurette", "extra", "extras",
    "behindthescenes", "behindscene", "makingof", "interview", "deletedscene",
}
EPISODE_RE = re.compile(r"(?i)(?:^|[ ._-])s(?P<season>\d{1,2})e(?P<episodes>\d{1,3}(?:[ ._-]*e\d{1,3})*)")
ALT_EPISODE_RE = re.compile(r"(?i)(?:^|[ ._-])(?P<season>\d{1,2})x(?P<episode>\d{1,3})(?:[ ._-]*-?[ ._-]*(?P<end>\d{1,3}))?")
DISC_RE = re.compile(r"(?i)^(?P<base>.*?)[ ._-]+(?:cd|disc|disk)[ ._-]*(?P<number>\d+)$")
PART_RE = re.compile(r"(?i)^(?P<base>.*?)[ ._-]+(?:(?:part|pt)[ ._-]*)?(?P<number>\d+)$")


@dataclass(slots=True)
class Detection:
    source: str = "filename"
    confidence: float = 0.0
    reason: str | None = None
    ambiguous: bool = False


@dataclass(slots=True)
class ClassifiedEntry:
    id: str
    kind: str
    title: str
    files: list[RepositoryFile]
    detection: Detection
    sequence: int | None = None
    season_number: int | None = None
    episode_numbers: list[int] = field(default_factory=list)


@dataclass(slots=True)
class FolderClassification:
    kind: str
    entries: list[ClassifiedEntry] = field(default_factory=list)
    gallery: list[RepositoryFile] = field(default_factory=list)
    extras: list[ClassifiedEntry] = field(default_factory=list)
    unclassified: list[RepositoryFile] = field(default_factory=list)
    primary_entry_id: str | None = None
    detection: Detection = field(default_factory=Detection)


def _stem(name: str) -> str:
    return os.path.splitext(name)[0]


def _normalized(value: str) -> str:
    value = unicodedata.normalize("NFKC", value).casefold()
    return "".join(character for character in value if character.isalnum())


def _tokens(value: str) -> set[str]:
    compact = _normalized(value)
    tokens = {_normalized(token) for token in re.split(r"[^\w]+", value) if token}
    return tokens | {word for word in EXTRA_WORDS if word in compact}


def _is_extra(row: RepositoryFile) -> bool:
    return bool(_tokens(_stem(row.name)) & EXTRA_WORDS)


def _entry_id(kind: str, rows: list[RepositoryFile]) -> str:
    media_ids = sorted(int(row.media_id) for row in rows if row.media_id is not None)
    return f"{kind}:{'-'.join(map(str, media_ids))}"


def _deduplicate(files: Iterable[RepositoryFile], primary_folder_id: int | None) -> list[RepositoryFile]:
    """Keep one physical row per Media, preferring the PRIMARY location."""
    chosen: dict[int, RepositoryFile] = {}
    for row in files:
        if row.media_id is None or row.materialize_status != "done":
            continue
        existing = chosen.get(int(row.media_id))
        if existing is None or (row.folder_id == primary_folder_id and existing.folder_id != primary_folder_id):
            chosen[int(row.media_id)] = row
    return sorted(chosen.values(), key=lambda row: (row.name.casefold(), row.id))


def _episode_numbers(match: re.Match[str]) -> tuple[int, list[int]]:
    season = int(match.group("season"))
    if "episodes" in match.groupdict():
        numbers = [int(value) for value in re.findall(r"\d+", match.group("episodes"))]
    else:
        start = int(match.group("episode"))
        end = int(match.group("end")) if match.group("end") else start
        numbers = list(range(start, end + 1)) if end >= start else [start, end]
    return season, numbers


def classify_folder(
    folder_name: str,
    files: Iterable[RepositoryFile],
    primary_folder_id: int | None = None,
) -> FolderClassification:
    rows = _deduplicate(files, primary_folder_id)
    artwork_or_preview: list[RepositoryFile] = []
    images: list[RepositoryFile] = []
    videos: list[RepositoryFile] = []
    for row in rows:
        stem = _stem(row.name).casefold()
        if stem in ARTWORK_STEMS or stem.startswith(("preview", "preivew")):
            artwork_or_preview.append(row)
        elif row.media_type == "IMAGE":
            images.append(row)
        elif row.media_type == "VIDEO":
            videos.append(row)

    extra_videos = [row for row in videos if _is_extra(row)]
    content_videos = [row for row in videos if row not in extra_videos]
    extras = [
        ClassifiedEntry(
            id=_entry_id("extra", [row]), kind="extra", title=_stem(row.name), files=[row],
            detection=Detection(confidence=0.95, reason="extra keyword in filename"),
        )
        for row in extra_videos
    ]

    episode_entries: list[ClassifiedEntry] = []
    remaining: list[RepositoryFile] = []
    for row in content_videos:
        match = EPISODE_RE.search(_stem(row.name)) or ALT_EPISODE_RE.search(_stem(row.name))
        if match is None:
            remaining.append(row)
            continue
        season, episodes = _episode_numbers(match)
        title = f"S{season:02d}E{episodes[0]:02d}"
        if len(episodes) > 1:
            title += f"-E{episodes[-1]:02d}"
        episode_entries.append(ClassifiedEntry(
            id=_entry_id("episode", [row]), kind="episode", title=title, files=[row],
            season_number=season, episode_numbers=episodes,
            detection=Detection(confidence=0.99, reason="season/episode pattern in filename"),
        ))

    if episode_entries:
        episode_entries.sort(key=lambda entry: (entry.season_number or 0, entry.episode_numbers, entry.id))
        return FolderClassification(
            kind="series", entries=episode_entries, gallery=images, extras=extras,
            unclassified=remaining,
            detection=Detection(
                confidence=0.99 if not remaining else 0.85,
                reason="season/episode filenames detected", ambiguous=bool(remaining),
            ),
        )

    # CD1/Disc2 are multiple physical files belonging to one logical feature.
    disc_groups: dict[str, list[tuple[int, RepositoryFile]]] = {}
    non_disc: list[RepositoryFile] = []
    for row in remaining:
        match = DISC_RE.match(_stem(row.name))
        if match is None:
            non_disc.append(row)
            continue
        disc_groups.setdefault(_normalized(match.group("base")), []).append((int(match.group("number")), row))
    valid_disc_groups = [group for group in disc_groups.values() if len(group) > 1]
    for group in disc_groups.values():
        if len(group) == 1:
            non_disc.append(group[0][1])
    if len(valid_disc_groups) == 1 and not non_disc:
        disc_rows = [row for _, row in sorted(valid_disc_groups[0], key=lambda item: item[0])]
        entry = ClassifiedEntry(
            id=_entry_id("feature", disc_rows), kind="feature", title=folder_name, files=disc_rows,
            detection=Detection(confidence=0.97, reason="CD/Disc segments detected"),
        )
        return FolderClassification(
            kind="movie", entries=[entry], gallery=images, extras=extras,
            primary_entry_id=entry.id, detection=entry.detection,
        )
    remaining = non_disc + [row for group in valid_disc_groups for _, row in group]

    # FolderName-1 / FolderName Part 2 are separate ordered works, not CD segments.
    parts: list[tuple[int, RepositoryFile]] = []
    unmatched: list[RepositoryFile] = []
    folder_key = _normalized(folder_name)
    for row in remaining:
        match = PART_RE.match(_stem(row.name))
        if match is not None and _normalized(match.group("base")) == folder_key:
            parts.append((int(match.group("number")), row))
        else:
            unmatched.append(row)
    if len(parts) > 1 and not unmatched:
        entries = [
            ClassifiedEntry(
                id=_entry_id("part", [row]), kind="part", title=f"{folder_name} - {number}",
                files=[row], sequence=number,
                detection=Detection(confidence=0.96, reason="folder-name numbered part pattern"),
            )
            for number, row in sorted(parts, key=lambda item: (item[0], item[1].name.casefold()))
        ]
        return FolderClassification(
            kind="multi_part", entries=entries, gallery=images, extras=extras,
            detection=Detection(confidence=0.96, reason="multiple numbered parts match folder name"),
        )

    remaining = [row for _, row in parts] + unmatched
    if len(remaining) == 1:
        row = remaining[0]
        exact_name = _normalized(_stem(row.name)) == folder_key
        if images and not exact_name:
            entry = ClassifiedEntry(
                id=_entry_id("video", [row]), kind="video", title=_stem(row.name), files=[row],
                detection=Detection(
                    confidence=0.6, reason="video name does not match image folder", ambiguous=True,
                ),
            )
            return FolderClassification(
                kind="mixed", entries=[entry], gallery=images, extras=extras,
                detection=Detection(
                    confidence=0.7, reason="unrelated video and gallery images coexist", ambiguous=True,
                ),
            )
        detection = Detection(
            confidence=0.98 if exact_name else 0.9,
            reason="video name matches folder" if exact_name else "only non-extra video in folder",
        )
        entry = ClassifiedEntry(
            id=_entry_id("feature", [row]), kind="feature", title=_stem(row.name), files=[row],
            detection=detection,
        )
        return FolderClassification(
            kind="movie", entries=[entry], gallery=images, extras=extras,
            primary_entry_id=entry.id, detection=detection,
        )

    if not remaining and images:
        return FolderClassification(
            kind="gallery", gallery=images, extras=extras,
            detection=Detection(confidence=0.98, reason="folder contains only gallery images"),
        )

    if remaining:
        entries = [
            ClassifiedEntry(
                id=_entry_id("video", [row]), kind="video", title=_stem(row.name), files=[row],
                detection=Detection(confidence=0.5, reason="unrelated video filename", ambiguous=True),
            )
            for row in sorted(remaining, key=lambda item: (item.name.casefold(), item.id))
        ]
        return FolderClassification(
            kind="mixed", entries=entries, gallery=images, extras=extras,
            detection=Detection(confidence=0.6, reason="multiple unrelated videos or mixed media", ambiguous=True),
        )

    return FolderClassification(
        kind="unknown", extras=extras, unclassified=artwork_or_preview,
        detection=Detection(confidence=0.0, reason="no classifiable content", ambiguous=True),
    )
