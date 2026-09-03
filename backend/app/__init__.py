"""FastAPI application factory with side-effect-free imports."""
from __future__ import annotations

from contextlib import asynccontextmanager
import logging
from logging.handlers import RotatingFileHandler
import os
from typing import Callable

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session
from sqlalchemy.orm import sessionmaker

from app.config import AppConfig, use_settings


def _configure_logging() -> None:
    """Install application handlers once per process."""
    root = logging.getLogger()
    if any(getattr(handler, "_media_manager_handler", False) for handler in root.handlers):
        return
    log_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "logs")
    os.makedirs(log_dir, exist_ok=True)
    formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    handlers = (
        RotatingFileHandler(
            os.path.join(log_dir, "app.log"),
            maxBytes=10 * 1024 * 1024,
            backupCount=5,
            encoding="utf-8",
        ),
        logging.StreamHandler(),
    )
    for handler in handlers:
        handler.setFormatter(formatter)
        handler._media_manager_handler = True  # type: ignore[attr-defined]
        root.addHandler(handler)
    root.setLevel(logging.INFO)


def _session_dependency(session_factory: Callable[[], Session]):
    def dependency():
        db = session_factory()
        try:
            yield db
        except Exception:
            db.rollback()
            raise
        finally:
            db.close()
    return dependency


def create_app(
    settings: AppConfig | None = None,
    *,
    session_factory: Callable[[], Session] | None = None,
    start_background_services: bool = True,
    validate_runtime: bool = True,
) -> FastAPI:
    """Build an isolated app; tests may replace sessions and disable workers."""
    from app.config import get_settings
    from app.models import get_db
    from app.modules import all_routers
    from app.runtime import BackgroundServiceManager
    from app.modules.sync.log_service import register_sync_listeners

    settings = settings or get_settings()
    owned_engine = None
    if session_factory is None:
        from app.shared.database import DATABASE_URL, create_sqlite_engine
        settings_database_url = f"sqlite:///{settings.get_db_path()}"
        if settings_database_url != DATABASE_URL:
            owned_engine = create_sqlite_engine(settings_database_url)
            session_factory = sessionmaker(autocommit=False, autoflush=False, bind=owned_engine)
    _configure_logging()
    logger = logging.getLogger(__name__)
    services = BackgroundServiceManager(
        enabled=start_background_services,
        settings=settings,
        session_factory=session_factory,
    )

    @asynccontextmanager
    async def lifespan(_app: FastAPI):
        with use_settings(settings):
            services.start()
            try:
                yield
            finally:
                services.stop()
                if owned_engine is not None:
                    owned_engine.dispose()

    application = FastAPI(
        title="媒体信息管理系统API",
        description="用于管理人员、分组、媒体资源和标签的后端接口",
        version="1.0.0",
        lifespan=lifespan,
    )
    application.state.settings = settings
    application.state.background_services = services

    @application.middleware("http")
    async def bind_runtime_settings(request, call_next):
        with use_settings(request.app.state.settings):
            return await call_next(request)
    application.add_middleware(
        CORSMiddleware,
        allow_origins=settings.ALLOWED_ORIGINS,
        allow_origin_regex=(
            r"^https?://(?:localhost|127\.0\.0\.1|10(?:\.\d{1,3}){3}|"
            r"192\.168(?:\.\d{1,3}){2}|172\.(?:1[6-9]|2\d|3[01])"
            r"(?:\.\d{1,3}){2})(?::\d+)?$"
        ),
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    if validate_runtime:
        settings.validate_repositories()
        if not os.path.isdir(settings.DATA_ROOT):
            raise RuntimeError(
                f"DATA_ROOT={settings.DATA_ROOT} 不存在。"
                "请运行 `uv run scripts/init_data_root.py` 初始化。"
            )
        for url_prefix, system_path in settings.get_static_mounts().items():
            if not os.path.isdir(system_path):
                logger.warning("[static] %s → %s 不存在,跳过挂载", url_prefix, system_path)
                continue
            application.mount(
                url_prefix, StaticFiles(directory=system_path), name=url_prefix.lstrip("/")
            )

    for router in all_routers:
        application.include_router(router)
    if session_factory is not None:
        application.dependency_overrides[get_db] = _session_dependency(session_factory)

    register_sync_listeners()
    if validate_runtime:
        settings.check_paths()
    return application


__all__ = ["create_app"]
