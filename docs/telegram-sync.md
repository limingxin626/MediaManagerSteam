# Telegram "Saved Messages" 自动同步

把 Telegram **Saved Messages**(跟自己对话)里的图片、视频、文件、纯文本、caption 自动同步进 backend DB。轮询式(默认 60s 一轮),与 backend 同机运行,直接调 service,不走 HTTP。

## 范围

- **进**:Saved Messages 中的 photo / video / document / 文本消息 / 带 caption 的媒体
- **打 tag**:每条入库消息**只**打 `#telegram` 一个 tag;caption 里的 `#xxx` 原文照传,**不**自动建 tag
- **作者**:`actor_id=NULL`(跟其他 importer 一致)
- **时间**:用 Telegram 原 `message.date` 作 `Message.created_at`

## 范围外

- 实时推送(本方案是 polling,延迟 ≤ 60s)
- 已导入消息的编辑/删除调和(轮询看不到)
- 群组、频道、bot 私聊等其他 chat(只监听 Saved Messages)
- 自动 hashtag 抽取(用户明确不要)
- Web UI 切换同步开关
- Bot token auth(用户客户端登录)

## 大文件策略(默认 50MB)

单文件 ≥ `TELEGRAM_LARGE_FILE_THRESHOLD` 字节(默认 50MB):

- **不**下载原文件
- **只**下载 Telegram 自带的 `document.thumb` 缩略图入库
- DB 同时建一行 `remote_media_reference` 记录:
  - `source_url`: `https://t.me/c/<user_id>/<msg_id>`(浏览器能打开)
  - `source_msg_id` + `source_chat_id`:程序化下载用
  - `original_filename` / `original_size` / `original_mime`:原文件元数据

日后想下载原文件,只要 `client.get_messages(chat_id, ids=msg_id)` 然后 `download_media(msg, file=...)` 即可。本期 UI 不实现,但数据已就绪。

查询当前所有未下载原文件的引用:

```sql
SELECT m.id, r.source_url, r.original_filename, r.original_size
FROM media m
JOIN remote_media_reference r ON r.media_id = m.id
ORDER BY r.created_at DESC;
```

## 前置条件

1. **my.telegram.org 申请 api credentials**:
   - 登录 → "API development tools" → 创建 app → 得到 `api_id` 和 `api_hash`
2. **Python 依赖已就绪**(`pyproject.toml` 里 `telethon>=1.36`)
3. **数据库迁移已跑**:
   ```bash
   cd backend
   uv run alembic upgrade head
   ```

## 环境变量

| 变量 | 必填 | 默认 | 说明 |
|------|------|------|------|
| `TELEGRAM_API_ID` | ✅ | — | my.telegram.org 申请的 id(整数) |
| `TELEGRAM_API_HASH` | ✅ | — | my.telegram.org 申请的 hash |
| `TELEGRAM_SESSION_PATH` | ❌ | `$DATA_ROOT/.telegram.session` | Telethon session 文件 |
| `TELEGRAM_INBOX_DIR` | ❌ | `$DATA_ROOT/telegram_inbox/` | 媒体下载暂存(`process_file` 会拷进 `uploads/`) |
| `TELEGRAM_POLL_INTERVAL` | ❌ | `60` | watch 模式轮询间隔(秒) |
| `TELEGRAM_LARGE_FILE_THRESHOLD` | ❌ | `52428800` (50MB) | 大于此字节数的文件只下载封面 |

`session` / `inbox` 默认放 `$DATA_ROOT` 而不是 backend 目录——session 含认证密钥,跟 DB 一起走,gitignored。

## 四种模式

```bash
cd backend

# 1. 首次:交互式登录(phone → code → 2FA),生成 .telegram.session
uv run scripts/telegram_sync.py bootstrap

# 2. 全量拉取(一次性,把 saved messages 历史全导进来)
uv run scripts/telegram_sync.py backfill

# 3. 单轮增量(cron / 手动触发)
uv run scripts/telegram_sync.py once

# 4. 长驻(watch 模式,后台跑)
uv run scripts/telegram_sync.py watch

# 或直接 ./start_telegram.sh(默认 watch,接第 1 个位置参数覆盖)
./start_telegram.sh            # watch
./start_telegram.sh once       # 单轮
./start_telegram.sh backfill   # 全量
./start_telegram.sh bootstrap  # 首次登录
```

## daemon 化(macOS launchd)

把下面保存为 `~/Library/LaunchAgents/com.media.telegram-sync.plist`,改占位符:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN"
  "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.media.telegram-sync</string>

    <key>ProgramArguments</key>
    <array>
        <string>/Users/<USER>/Code/MediaManagerSteam/backend/start_telegram.sh</string>
        <string>watch</string>
    </array>

    <key>WorkingDirectory</key>
    <string>/Users/<USER>/Code/MediaManagerSteam/backend</string>

    <key>EnvironmentVariables</key>
    <dict>
        <key>DATA_ROOT</key>
        <string>/Users/<USER>/data/Media/</string>
        <key>TELEGRAM_API_ID</key>
        <string><YOUR_API_ID></string>
        <key>TELEGRAM_API_HASH</key>
        <string><YOUR_API_HASH></string>
        <key>PATH</key>
        <string>/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin</string>
    </dict>

    <key>RunAtLoad</key>
    <true/>

    <key>KeepAlive</key>
    <dict>
        <key>SuccessfulExit</key>
        <false/>
        <key>Crashed</key>
        <true/>
    </dict>

    <key>StandardOutPath</key>
    <string>/tmp/telegram-sync.out.log</string>
    <key>StandardErrorPath</key>
    <string>/tmp/telegram-sync.err.log</string>

    <key>ThrottleInterval</key>
    <integer>30</integer>
</dict>
</plist>
```

加载:

```bash
launchctl load ~/Library/LaunchAgents/com.media.telegram-sync.plist
launchctl start com.media.telegram-sync
# 看日志
tail -f /tmp/telegram-sync.err.log
# 卸载
launchctl unload ~/Library/LaunchAgents/com.media.telegram-sync.plist
```

plist 不放在 repo 里 —— 每台机器路径不同,放 repo 会变成废模板。

## 故障排查

| 现象 | 排查 |
|------|------|
| `TELEGRAM_API_ID / TELEGRAM_API_HASH 未设置` | export 一下,或写到 `.env` |
| `未找到 session 文件` | 先跑 `bootstrap` 登录 |
| `session 已过期或无效` | 同上,重新 `bootstrap` |
| 轮询卡住没新消息 | 查 DB:`SELECT * FROM telegram_sync_state` 看 `last_sync_at` 和 `last_error` |
| `last_error: FloodWait:Ns` | TG 限流,代码会自动退避 N+5 秒,无需手动干预 |
| 想从头重导历史 | `sqlite3 $DATA_ROOT/db.sqlite3 "DELETE FROM telegram_sync_state;"` 然后 `backfill` —— 已 import 的媒体因为 hash dedup,不会被重复创建 |
| 想看某条消息有没有进 | `SELECT m.* FROM message m JOIN message_tag mt ON mt.message_id=m.id JOIN tag t ON t.id=mt.tag_id WHERE t.name='#telegram' ORDER BY m.id DESC LIMIT 5;` |
| 想看哪些是大文件 | `SELECT r.*, m.id as media_id FROM remote_media_reference r JOIN media m ON r.media_id=m.id;` |

## 关键约定

- **dedup**:`process_file()` 按 Blake2b hash dedup,同一张图被保存到 N 个 saved message 也只产生一个 `Media` 行
- **失败隔离**:一条消息 raise 不会让整批失败 —— `db.rollback()` 后继续下一条;`last_message_id` 只在成功后前进,失败消息下轮会重试
- **transaction**:`create_message_with_files(commit=True)` 内部整组(album)原子,中间失败会 rollback 整组 —— 这意味着 album 里任何一张图坏掉,整组都不会入库,下轮整组重拉
- **no hashtag extraction**:`create_message_with_files` 只看 `tag_ids`,不会从 caption 抽 `#xxx` 建 tag