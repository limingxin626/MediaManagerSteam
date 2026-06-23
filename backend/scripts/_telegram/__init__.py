"""Telegram "Saved Messages" 同步内部包。

不在 `app/services` 下,因为:
1. 这是一个 importer / sync runner,不暴露 HTTP 接口,不属于 service 层。
2. 它的依赖(telethon, async runtime)是边车型的,不应该污染 backend 核心 deps。

入口:`scripts/telegram_sync.py`
"""