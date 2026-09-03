from types import SimpleNamespace

from app.modules.repository.folder_classifier import artwork_kind, classify_folder


def media_file(file_id: int, name: str, media_type: str):
    return SimpleNamespace(
        id=file_id, media_id=file_id, folder_id=1, name=name,
        media_type=media_type, materialize_status="done",
    )


def test_single_video_is_movie_and_primary():
    result = classify_folder("Interstellar", [
        media_file(1, "Interstellar.mp4", "VIDEO"),
        media_file(2, "poster.jpg", "IMAGE"),
        media_file(3, "fanart.jpg", "IMAGE"),
    ], 1)

    assert result.kind == "movie"
    assert result.primary_entry_id == result.entries[0].id
    assert [row.name for row in result.entries[0].files] == ["Interstellar.mp4"]
    assert result.detection.confidence == 0.98


def test_numbered_folder_name_files_are_separate_parts():
    result = classify_folder("Documentary", [
        media_file(1, "Documentary-2.mp4", "VIDEO"),
        media_file(2, "Documentary-1.mp4", "VIDEO"),
    ], 1)

    assert result.kind == "multi_part"
    assert [entry.sequence for entry in result.entries] == [1, 2]
    assert [entry.kind for entry in result.entries] == ["part", "part"]
    assert result.primary_entry_id is None


def test_cd_files_are_segments_of_one_movie():
    result = classify_folder("Long Movie", [
        media_file(1, "Long Movie CD2.mp4", "VIDEO"),
        media_file(2, "Long Movie CD1.mp4", "VIDEO"),
    ], 1)

    assert result.kind == "movie"
    assert len(result.entries) == 1
    assert [row.name for row in result.entries[0].files] == [
        "Long Movie CD1.mp4", "Long Movie CD2.mp4",
    ]


def test_standard_episodes_make_series():
    result = classify_folder("Show", [
        media_file(1, "Show.S01E02.mp4", "VIDEO"),
        media_file(2, "Show.S01E01-E02.mp4", "VIDEO"),
        media_file(3, "Show.S00E01.mp4", "VIDEO"),
    ], 1)

    assert result.kind == "series"
    assert [(entry.season_number, entry.episode_numbers) for entry in result.entries] == [
        (0, [1]), (1, [1, 2]), (1, [2]),
    ]


def test_only_images_make_gallery_but_artwork_is_excluded():
    result = classify_folder("Photos", [
        media_file(1, "001.jpg", "IMAGE"),
        media_file(2, "002.jpg", "IMAGE"),
        media_file(3, "poster.jpg", "IMAGE"),
    ], 1)

    assert result.kind == "gallery"
    assert [row.name for row in result.gallery] == ["001.jpg", "002.jpg"]


def test_unrelated_videos_and_images_make_mixed_and_extract_extras():
    result = classify_folder("Event", [
        media_file(1, "opening.mp4", "VIDEO"),
        media_file(2, "interview.mp4", "VIDEO"),
        media_file(3, "closing.mp4", "VIDEO"),
        media_file(4, "IMG_001.jpg", "IMAGE"),
    ], 1)

    assert result.kind == "mixed"
    assert [entry.title for entry in result.entries] == ["closing", "opening"]
    assert [entry.title for entry in result.extras] == ["interview"]
    assert [row.name for row in result.gallery] == ["IMG_001.jpg"]
    assert result.detection.ambiguous is True


def test_one_unrelated_video_with_images_is_mixed_not_movie():
    result = classify_folder("Event Photos", [
        media_file(1, "opening.mp4", "VIDEO"),
        media_file(2, "IMG_001.jpg", "IMAGE"),
        media_file(3, "IMG_002.jpg", "IMAGE"),
    ], 1)

    assert result.kind == "mixed"
    assert result.primary_entry_id is None
    assert result.entries[0].kind == "video"
    assert [row.name for row in result.gallery] == ["IMG_001.jpg", "IMG_002.jpg"]


def test_mirror_duplicates_prefer_primary_physical_file():
    primary = media_file(10, "Movie.mp4", "VIDEO")
    mirror = media_file(20, "Renamed.mp4", "VIDEO")
    mirror.media_id = primary.media_id
    mirror.folder_id = 2

    result = classify_folder("Movie", [mirror, primary], 1)

    assert [row.name for row in result.entries[0].files] == ["Movie.mp4"]


def test_artwork_kind_matches_primary_and_prefixed_variants():
    assert artwork_kind("fanart.jpg") == ("fanart", None)
    assert artwork_kind("poster.PNG") == ("poster", None)
    assert artwork_kind("MovieName-fanart.jpg") == ("fanart", None)
    assert artwork_kind("Movie (2020).poster.jpg") == ("poster", None)
    assert artwork_kind("MovieName_fanart1.jpg") == ("fanart", 1)
    assert artwork_kind("MovieName-fanart2.jpg") == ("fanart", 2)
    assert artwork_kind("fanart1.png") == ("fanart", 1)
    assert artwork_kind("photo.jpg") is None
    assert artwork_kind("fanart-wallpaper.jpg") is None  # 类型词不在末尾


def test_prefixed_and_numbered_fanart_excluded_from_gallery():
    result = classify_folder("Movie", [
        media_file(1, "Movie.mp4", "VIDEO"),
        media_file(2, "Movie-fanart.jpg", "IMAGE"),
        media_file(3, "Movie-fanart1.jpg", "IMAGE"),
        media_file(4, "Movie-poster.jpg", "IMAGE"),
    ], 1)

    assert result.kind == "movie"
    assert [row.name for row in result.entries[0].files] == ["Movie.mp4"]
    assert result.gallery == []
