from .actor import router as actor_router
from .message import router as message_router
from .media import router as media_router
from .files import router as files_router
from .tags import router as tags_router
from .sync import router as sync_router
from .admin import router as admin_router
from .dashboard import router as dashboard_router
from .todos import router as todos_router

# 所有路由列表
all_routers = [
    actor_router,
    message_router,
    media_router,
    files_router,
    tags_router,
    sync_router,
    admin_router,
    dashboard_router,
    todos_router,
]
