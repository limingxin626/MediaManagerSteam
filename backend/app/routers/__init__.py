from .actor import router as actor_router
from .message import router as message_router
from .media import router as media_router
from .files import router as files_router
from .tags import router as tags_router
from .sync import router as sync_router
from .admin import router as admin_router
from .dashboard import router as dashboard_router
from .issues import router as issues_router
from .health import router as health_router
from .smart import router as smart_router

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
    issues_router,
    health_router,
    smart_router,
]
