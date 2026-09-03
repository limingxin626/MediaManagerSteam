"""Business-domain modules and the application's router registry."""
from fastapi import APIRouter

from app.modules.collection.router import router as collection_router
from app.modules.issue.router import router as issue_router
from app.modules.media.router import router as media_router
from app.modules.message.router import router as message_router
from app.modules.person.router import router as person_router
from app.modules.repository.file_router import router as file_router
from app.modules.repository.folder_router import router as folder_router
from app.modules.repository.router import router as repository_router
from app.modules.smart.router import router as smart_router
from app.modules.sync.router import router as sync_router
from app.modules.system.admin_router import router as admin_router
from app.modules.system.dashboard_router import router as dashboard_router
from app.modules.system.health_router import router as health_router
from app.modules.tag.router import router as tag_router
from app.modules.todo.router import router as todo_router
from app.modules.transaction.router import router as transaction_router

all_routers: tuple[APIRouter, ...] = (
    collection_router, person_router, message_router, media_router, file_router,
    tag_router, sync_router, admin_router, dashboard_router, issue_router,
    health_router, smart_router, transaction_router, repository_router,
    folder_router, todo_router,
)

__all__ = ["all_routers"]
