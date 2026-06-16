"""
初始化 DATA_ROOT:建子目录 + 写 repositories.json 模板。
幂等,可重复跑(--force 覆盖 repositories.json)。

用法:
    cd backend
    uv run scripts/init_data_root.py
    uv run scripts/init_data_root.py --data-root /custom/path
    uv run scripts/init_data_root.py --default-repo-path /Volumes/X/Uploads
    uv run scripts/init_data_root.py --force   # 覆盖现有 repositories.json

完整新机器流程:
    1. uv run scripts/init_data_root.py
    2. 编辑 $DATA_ROOT/repositories.json,把所有 platform 的 paths 填好
    3. uv run alembic upgrade head
    4. uv run api.py
"""
import argparse
import json
import logging
import os
import sys

REPOSITORIES_FILENAME = "repositories.json"
SUBDIRS = ("thumbs", "preview", "actor_cover")


def platform_key() -> str:
    if sys.platform == "darwin":
        return "darwin"
    if sys.platform == "win32":
        return "windows"
    return "linux"


def main() -> None:
    ap = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    ap.add_argument(
        "--data-root",
        default=os.getenv("DATA_ROOT", "").strip(),
        help="DATA_ROOT 绝对路径(默认读 env var)",
    )
    ap.add_argument(
        "--default-repo-path",
        default=None,
        help="default_repo 'uploads' 的绝对路径(默认: <DATA_ROOT>/uploads)。"
             "外接盘场景请显式传。",
    )
    ap.add_argument(
        "--force",
        action="store_true",
        help="覆盖已存在的 repositories.json",
    )
    args = ap.parse_args()

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
    )
    log = logging.getLogger("init_data_root")

    if not args.data_root:
        sys.exit("DATA_ROOT 未设置。export DATA_ROOT=... 或 --data-root=...")
    data_root = os.path.abspath(args.data_root)
    parent = os.path.dirname(data_root) or "."
    if not os.path.isdir(parent):
        sys.exit(f"父目录 {parent} 不存在,请先创建")

    # DATA_ROOT + 三个子目录 + default repo
    os.makedirs(data_root, exist_ok=True)
    log.info("✓ DATA_ROOT=%s", data_root)
    for sub in SUBDIRS:
        os.makedirs(os.path.join(data_root, sub), exist_ok=True)
        log.info("✓ %s/", sub)

    default_repo = args.default_repo_path or os.path.join(data_root, "uploads")
    os.makedirs(default_repo, exist_ok=True)
    log.info("✓ default_repo 'uploads' → %s", default_repo)

    # repositories.json 模板(已存在则跳过,除非 --force)
    repo_json = os.path.join(data_root, REPOSITORIES_FILENAME)
    if os.path.isfile(repo_json) and not args.force:
        log.info("repositories.json 已存在,跳过(用 --force 覆盖): %s", repo_json)
    else:
        plat = platform_key()
        template = {
            "version": 1,
            "default_repo_id": "uploads",
            "repositories": {
                "uploads": {
                    "human_name": "Uploads",
                    "paths": {plat: default_repo},
                },
            },
        }
        with open(repo_json, "w", encoding="utf-8") as f:
            json.dump(template, f, indent=2, ensure_ascii=False)
        log.info("✓ repositories.json(请编辑 paths 填好所有 platform)")

    log.info("✅ 初始化完成。")
    log.info("  下一步: 编辑 %s 设置实际路径(尤其是外接盘)", repo_json)
    log.info("  然后:   uv run alembic upgrade head  &&  uv run api.py")


if __name__ == "__main__":
    main()
