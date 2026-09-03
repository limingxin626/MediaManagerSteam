import ast
import io
from pathlib import Path

import pytest

from app.config import AppConfig, use_settings
from app.modules.repository import file_service


APP_ROOT = Path(__file__).parents[1] / "app"


def _imports(path: Path):
    tree = ast.parse(path.read_text(encoding="utf-8"))
    for node in ast.walk(tree):
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            yield node


def test_domain_implementation_modules_do_not_depend_on_fastapi():
    offenders = []
    paths = list(APP_ROOT.glob("modules/**/*service.py")) + list(APP_ROOT.glob("modules/**/queries.py"))
    for path in paths:
        for node in _imports(path):
            names = [node.module] if isinstance(node, ast.ImportFrom) else [alias.name for alias in node.names]
            if any(name and name.startswith("fastapi") for name in names):
                offenders.append(path.relative_to(APP_ROOT).as_posix())
    assert offenders == []


def test_orm_leaf_modules_import_base_from_shared_database():
    offenders = []
    for path in (APP_ROOT / "models").glob("*.py"):
        if path.name == "__init__.py":
            continue
        if "from app.models import Base" in path.read_text(encoding="utf-8"):
            offenders.append(path.name)
    assert offenders == []


def test_router_modules_do_not_execute_database_operations():
    forbidden = {"query", "get", "execute", "add", "delete", "flush", "commit", "rollback", "refresh"}
    offenders = []
    for path in APP_ROOT.glob("modules/**/*router.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if (
                isinstance(node, ast.Call)
                and isinstance(node.func, ast.Attribute)
                and isinstance(node.func.value, ast.Name)
                and node.func.value.id == "db"
                and node.func.attr in forbidden
            ):
                offenders.append(f"{path.relative_to(APP_ROOT).as_posix()}:{node.lineno}")
    assert offenders == []


def test_file_service_sandboxes_all_paths(tmp_path):
    data = tmp_path / "data"
    repo = tmp_path / "repo"
    data.mkdir()
    repo.mkdir()
    settings = AppConfig(data_root=str(data), repositories={"repo": str(repo)}, default_repo_id="repo", load_repositories=False)
    with use_settings(settings):
        file_service.create_path("repo", "album", "directory")
        uploaded = file_service.upload_file(io.BytesIO(b"ok"), "../photo.jpg", "repo", "album")
        assert uploaded.path == "album/photo.jpg"
        assert (repo / "album" / "photo.jpg").read_bytes() == b"ok"
        with pytest.raises(file_service.UnsafePathError):
            file_service.resolve_path("repo", "../outside.txt")
        with pytest.raises(file_service.UnsafePathError):
            file_service.resolve_path("repo", str(tmp_path / "outside.txt"))
        with pytest.raises(file_service.UnsafePathError):
            file_service.delete_path("repo", "")


def test_config_instances_do_not_share_repository_state(tmp_path):
    first = AppConfig(data_root=str(tmp_path / "one"), repositories={"one": str(tmp_path / "r1")}, default_repo_id="one", load_repositories=False)
    second = AppConfig(data_root=str(tmp_path / "two"), repositories={"two": str(tmp_path / "r2")}, default_repo_id="two", load_repositories=False)
    assert first.get_repositories() == {"one": str((tmp_path / "r1").resolve())}
    assert second.get_repositories() == {"two": str((tmp_path / "r2").resolve())}
    assert first.DATA_ROOT != second.DATA_ROOT
