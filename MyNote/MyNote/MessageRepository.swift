//
//  MessageRepository.swift
//  MyNote
//
//  数据访问层 —— 消息流(message + message_media + tag + media_tag + actor + issue)。
//
//  设计要点:
//    1. 与 MediaRepository 同构:对外提供 cursor 分页 list + 过滤 + 批量预取,
//       避免每条消息单独查 tag / actor / media(否则消息流加载 N+1 必爆)。
//    2. SQL 过滤语义与 backend `app/routers/message.py::_build_detail_query` 1:1 对齐
//       (actorId == 0 → IS NULL,tagId 走「message_tag ∪ media_tag」并集,等等),
//       保证 Mac 直读结果与 web 经 backend 拉到的结果一致。
//    3. cursor 用 ISO created_at 字符串(无 id 兜底),与 vue 端 Message.vue 同协议,
//       GRDB 端不需要复合 cursor —— 消息量级在千条以内,同毫秒多条不构成实际
//       性能问题(若真出问题再加 `(created_at, id)` 复合,接口形态不变)。
//    4. 媒体预览上限 9 张(MEDIA_PREVIEW_LIMIT=9,后端约定),保持与 web 端
//       3x3 宫格一致;detail 拉取时不限,feed 列表限制 9 张避免单条 SQL 返回过大。
//

import Foundation
import GRDB

/// 消息域分页 list / 详情 / 过滤 / timeline 的过滤参数。
///
/// 约定:
/// - `nil` = 不过滤
/// - 0    = 「无 actor」/「无 issue」(`actorId == 0` / `issueId == 0` 在 SQL 里
///         转成 `IS NULL`)
/// - 正整数 = `actor_id = ?` / `issue_id = ?`
struct MessageFilter: Equatable {
    var actorId: Int? = nil
    var tagId: Int? = nil
    var issueId: Int? = nil
    var queryText: String? = nil
    var mediaId: Int? = nil
    var starredOnly: Bool = false
}

final class MessageRepository {
    private let database: LocalDatabase
    /// 消息内媒体预览上限 3x3 = 9,与 backend `MEDIA_PREVIEW_LIMIT` 一致。
    private static let mediaPreviewLimit = 9

    init(database: LocalDatabase = .shared) {
        self.database = database
    }

    // MARK: - 列表(feed)

    /// 取一页 Message + 关联 actor + media_items(限 9) + tags(经 message_tag ∪ media_tag 去重)。
    /// 排序按 `created_at DESC, id DESC`,匹配 vue 端 Message.vue 的「最新优先」语义。
    func list(
        cursor: String?,
        limit: Int,
        filter: MessageFilter
    ) async throws -> (items: [Message], nextCursor: String?, hasMore: Bool) {
        guard let queue = database.queue else { throw RepositoryError.databaseNotOpen }

        let cursorDate: Date? = try cursor.map { try MessageCursor.decode($0) }

        return try await queue.read { db -> (items: [Message], nextCursor: String?, hasMore: Bool) in
            // 1) 主查询:按过滤条件 + 排序 + limit + 1
            var where_: [String] = []
            var args: [DatabaseValueConvertible] = []

            if let d = cursorDate {
                where_.append("created_at < ?")
                args.append(d)
            }
            Self.appendFilter(filter, where: &where_, args: &args)

            let whereClause = where_.isEmpty ? "" : "WHERE \(where_.joined(separator: " AND "))"
            let sql = """
                SELECT * FROM message
                \(whereClause)
                ORDER BY created_at DESC, id DESC
                LIMIT ?
                """
            var allArgs = args
            allArgs.append(limit + 1)

            let rows = try MessageRecord.fetchAll(db, sql: sql, arguments: StatementArguments(allArgs))
            let hasMore = rows.count > limit
            let page = hasMore ? Array(rows.prefix(limit)) : rows

            guard !page.isEmpty else {
                return ([], nil, false)
            }

            let nextCursor: String? = {
                guard hasMore, let last = page.last else { return nil }
                return MessageCursor.encode(last.createdAt)
            }()

            // 2) 批量加载 actor
            let actorIds = Set(page.compactMap { $0.actorId })
            let actorById = try Self.fetchActorsById(db: db, ids: Array(actorIds))

            // 3) 批量加载 media items(限 9 / message)
            let messageIds = page.map { $0.id }
            let mediaByMsg = try Self.fetchMediaItemsByMessage(
                db: db, messageIds: messageIds, perMessageLimit: Self.mediaPreviewLimit
            )

            // 4) 批量加载 tags(message_tag ∪ media_tag 去重,沿用 backend `_aggregate_tags`)
            let tagByMsg = try Self.fetchAggregatedTags(
                db: db, messageIds: messageIds, mediaByMsg: mediaByMsg
            )

            let items: [Message] = page.map { rec in
                let actor = rec.actorId.flatMap { actorById[$0] }
                let mediaItems = mediaByMsg[rec.id] ?? []
                let tags = tagByMsg[rec.id] ?? []
                return rec.toUIModel(
                    actor: actor,
                    mediaItems: mediaItems,
                    tags: tags
                )
            }

            return (items, nextCursor, hasMore)
        }
    }

    // MARK: - 单条详情(无媒体数量限制)

    /// 取单条 message 的完整数据(actor + 全部 media_items + tags),
    /// 供 detail 面板点击消息卡时拉取。
    func fetchMessageDetail(id: Int) async throws -> Message? {
        guard let queue = database.queue else { throw RepositoryError.databaseNotOpen }

        return try await queue.read { db -> Message? in
            guard let rec = try MessageRecord.fetchOne(db, sql: "SELECT * FROM message WHERE id = ?", arguments: [id]) else {
                return nil
            }

            let actor = rec.actorId.flatMap { try? Self.fetchActorsById(db: db, ids: [$0])[$0] }
            let mediaByMsg = try Self.fetchMediaItemsByMessage(
                db: db, messageIds: [rec.id], perMessageLimit: nil
            )
            let tagByMsg = try Self.fetchAggregatedTags(
                db: db, messageIds: [rec.id], mediaByMsg: mediaByMsg
            )

            return rec.toUIModel(
                actor: actor,
                mediaItems: mediaByMsg[rec.id] ?? [],
                tags: tagByMsg[rec.id] ?? []
            )
        }
    }

    // MARK: - 过滤侧栏条目

    /// 一次拉取 tags / actors / issues 三个集合,供 FilterSidebar 渲染。
    /// - tags:全部 tag,按消息数降序
    /// - actors:全部 actor,按消息数降序,加「无演员」占位(actorId == 0)
    /// - issues:status = 'doing',按 created_at DESC;前端加「无 issue」占位
    func fetchFilters() async throws -> (tags: [Tag], actors: [Actor], issues: [Issue]) {
        guard let queue = database.queue else { throw RepositoryError.databaseNotOpen }

        return try await queue.read { db -> (tags: [Tag], actors: [Actor], issues: [Issue]) in
            let tags = try Self.fetchTagsWithCount(db: db)
            let actors = try Self.fetchActorsWithCount(db: db)
            let issues = try Self.fetchDoingIssues(db: db)
            return (tags, actors, issues)
        }
    }

    // MARK: - 时间线(月份)

    /// 某年某月有消息的日期 + 消息数,只读 message 表。
    /// filters 与 list 共享同一过滤语义,保证 timeline 计数与 feed 命中数一致。
    func monthlyDayCount(
        year: Int,
        month: Int,
        filter: MessageFilter
    ) async throws -> [TimelineEntry] {
        guard let queue = database.queue else { throw RepositoryError.databaseNotOpen }

        // 月初/下月初
        var startComp = DateComponents()
        startComp.year = year; startComp.month = month; startComp.day = 1
        guard let monthStart = Calendar.current.date(from: startComp),
              let monthEnd = Calendar.current.date(byAdding: .month, value: 1, to: monthStart)
        else { return [] }

        return try await queue.read { db -> [TimelineEntry] in
            var where_: [String] = []
            var args: [DatabaseValueConvertible] = []

            // 限定月份:[月初, 下月初)
            where_.append("created_at >= ? AND created_at < ?")
            args.append(monthStart)
            args.append(monthEnd)

            Self.appendFilter(filter, where: &where_, args: &args)

            let whereClause = "WHERE \(where_.joined(separator: " AND "))"
            let sql = """
                SELECT
                    CAST(strftime('%Y', created_at) AS INTEGER) AS year,
                    CAST(strftime('%m', created_at) AS INTEGER) AS month,
                    CAST(strftime('%d', created_at) AS INTEGER) AS day,
                    COUNT(*) AS count
                FROM message
                \(whereClause)
                GROUP BY year, month, day
                ORDER BY year DESC, month DESC, day DESC
                """
            let rows = try Row.fetchAll(db, sql: sql, arguments: StatementArguments(args))
            return rows.map { row in
                TimelineEntry(
                    year: row["year"],
                    month: row["month"],
                    day: row["day"],
                    count: row["count"]
                )
            }
        }
    }

    // MARK: - SQL builder

    /// 共享过滤拼装 —— 跟 backend `_build_detail_query` 的语义保持一致:
    /// - `actorId == 0`  → `actor_id IS NULL`
    /// - `actorId > 0`   → `actor_id = ?`
    /// - `issueId == 0`  → `issue_id IS NULL`
    /// - `issueId > 0`   → `issue_id = ?`
    /// - `tagId > 0`     → `id IN (SELECT message_id FROM message_tag WHERE tag_id = ?
    ///                      UNION
    ///                      SELECT message_id FROM message_media
    ///                        JOIN media_tag ON media_tag.media_id = message_media.media_id
    ///                        WHERE media_tag.tag_id = ?)`
    /// - `mediaId > 0`   → `id IN (SELECT message_id FROM message_media WHERE media_id = ?)`
    /// - `queryText`     → `text LIKE '%' || ? || '%'`
    /// - `starredOnly`   → `starred = 1`
    private static func appendFilter(
        _ f: MessageFilter,
        where where_: inout [String],
        args: inout [DatabaseValueConvertible]
    ) {
        if let aid = f.actorId {
            if aid == 0 {
                where_.append("actor_id IS NULL")
            } else {
                where_.append("actor_id = ?")
                args.append(aid)
            }
        }
        if let iid = f.issueId {
            if iid == 0 {
                where_.append("issue_id IS NULL")
            } else {
                where_.append("issue_id = ?")
                args.append(iid)
            }
        }
        if let q = f.queryText, !q.isEmpty {
            where_.append("text LIKE '%' || ? || '%'")
            args.append(q)
        }
        if let mid = f.mediaId, mid > 0 {
            where_.append("id IN (SELECT message_id FROM message_media WHERE media_id = ?)")
            args.append(mid)
        }
        if let tid = f.tagId, tid > 0 {
            where_.append("""
                id IN (
                    SELECT message_id FROM message_tag WHERE tag_id = ?
                    UNION
                    SELECT message_id FROM message_media
                        JOIN media_tag ON media_tag.media_id = message_media.media_id
                    WHERE media_tag.tag_id = ?
                )
                """)
            args.append(tid)
            args.append(tid)
        }
        if f.starredOnly {
            where_.append("starred = 1")
        }
    }

    // MARK: - 批量预取:actor

    private static func fetchActorsById(db: Database, ids: [Int]) throws -> [Int: ActorRecord] {
        guard !ids.isEmpty else { return [:] }
        let placeholders = Array(repeating: "?", count: ids.count).joined(separator: ",")
        let sql = "SELECT * FROM actor WHERE id IN (\(placeholders))"
        let rows = try ActorRecord.fetchAll(db, sql: sql, arguments: StatementArguments(ids.map { $0 as DatabaseValueConvertible }))
        var out: [Int: ActorRecord] = [:]
        for r in rows { out[r.id] = r }
        return out
    }

    /// 演员 + 消息数,按消息数降序;「无演员」占位不在 SQL 里(UI 层加)。
    private static func fetchActorsWithCount(db: Database) throws -> [Actor] {
        let sql = """
            SELECT a.id, a.name, a.avatar_path, COUNT(m.id) AS message_count
            FROM actor a
            LEFT JOIN message m ON m.actor_id = a.id
            GROUP BY a.id
            ORDER BY message_count DESC, a.name ASC
            """
        let rows = try Row.fetchAll(db, sql: sql)
        return rows.map { row in
            Actor(
                id: row["id"],
                name: row["name"],
                avatarPath: row["avatar_path"],
                messageCount: row["message_count"]
            )
        }
    }

    // MARK: - 批量预取:media items

    /// 一批 message 的 media_items(按 position 排序),组装成 [Media] UI 模型。
    /// 复用 `Media` UI struct 与 `MessageMediaItem` UI struct。
    /// `perMessageLimit == nil` → 不限(供 detail);否则按 position 截断到 N(feed 列表 9 张)。
    private static func fetchMediaItemsByMessage(
        db: Database,
        messageIds: [Int],
        perMessageLimit: Int?
    ) throws -> [Int: [MessageMediaItem]] {
        guard !messageIds.isEmpty else { return [:] }
        let placeholders = Array(repeating: "?", count: messageIds.count).joined(separator: ",")
        let sql = """
            SELECT mm.message_id, mm.position,
                   m.id AS m_id, m.file_path, m.repo_id, m.mime_type, m.width, m.height,
                   m.duration_ms, m.starred AS m_starred,
                   m.created_at AS m_created_at, m.updated_at AS m_updated_at,
                   m.video_media_id, m.frame_ms, m.start_ms, m.end_ms
            FROM message_media mm
            JOIN media m ON m.id = mm.media_id
            WHERE mm.message_id IN (\(placeholders))
            ORDER BY mm.message_id, mm.position
            """
        let rows = try Row.fetchAll(db, sql: sql, arguments: StatementArguments(messageIds.map { $0 as DatabaseValueConvertible }))

        // 收集本页出现的 media id,批量取它们的 tag
        var mediaIds = Set<Int>()
        var grouped: [Int: [(position: Int, media: MediaRecord)]] = [:]
        for row in rows {
            let msgId: Int = row["message_id"]
            let position: Int = row["position"]
            let rec = MediaRecord(
                id: row["m_id"],
                filePath: row["file_path"],
                repoId: row["repo_id"],
                fileHash: nil,
                fileSize: nil,
                mimeType: row["mime_type"],
                width: row["width"],
                height: row["height"],
                durationMs: row["duration_ms"],
                takenAt: nil,
                gpsLat: nil,
                gpsLng: nil,
                orientation: nil,
                cameraMake: nil,
                cameraModel: nil,
                lens: nil,
                videoCodec: nil,
                audioCodec: nil,
                hasAudio: nil,
                fps: nil,
                bitrate: nil,
                rating: 0,
                starred: row["m_starred"] ?? 0,
                viewCount: 0,
                lastViewedAt: nil,
                createdAt: row["m_created_at"],
                updatedAt: row["m_updated_at"],
                videoMediaId: row["video_media_id"],
                frameMs: row["frame_ms"],
                startMs: row["start_ms"],
                endMs: row["end_ms"]
            )
            grouped[msgId, default: []].append((position, rec))
            mediaIds.insert(rec.id)
        }

        // 批量取 media tag
        let tagByMedia = try fetchTagsByMedia(db: db, mediaIds: Array(mediaIds))

        // 组装 MessageMediaItem,带 per-message 截断
        var out: [Int: [MessageMediaItem]] = [:]
        for (msgId, var entries) in grouped {
            entries.sort { $0.position < $1.position }
            if let limit = perMessageLimit, entries.count > limit {
                entries = Array(entries.prefix(limit))
            }
            out[msgId] = entries.map { entry -> MessageMediaItem in
                let media = entry.media.toUIModel(tags: tagByMedia[entry.media.id] ?? [])
                return MessageMediaItem(from: media)
            }
        }
        return out
    }

    // MARK: - 批量预取:tag(message_tag ∪ media_tag 去重)

    /// 沿用 backend `_aggregate_tags`:
    ///   1. 收集该 message 直连的 tag
    ///   2. 再加上该 message 关联的 media 携带的 tag
    ///   3. 按 tag.id 去重,保持 (1) 优先出现的顺序
    private static func fetchAggregatedTags(
        db: Database,
        messageIds: [Int],
        mediaByMsg: [Int: [MessageMediaItem]]
    ) throws -> [Int: [MessageTag]] {
        guard !messageIds.isEmpty else { return [:] }
        let placeholders = Array(repeating: "?", count: messageIds.count).joined(separator: ",")

        // (1) message 直连 tag
        let directSQL = """
            SELECT mt.message_id, t.id, t.name, t.category
            FROM message_tag mt
            JOIN tag t ON t.id = mt.tag_id
            WHERE mt.message_id IN (\(placeholders))
            """
        let directRows = try Row.fetchAll(
            db, sql: directSQL,
            arguments: StatementArguments(messageIds.map { $0 as DatabaseValueConvertible })
        )
        var result: [Int: [MessageTag]] = [:]
        var seenByMsg: [Int: Set<Int>] = [:]
        for row in directRows {
            let msgId: Int = row["message_id"]
            let tag = MessageTag(id: row["id"], name: row["name"], category: row["category"])
            result[msgId, default: []].append(tag)
            seenByMsg[msgId, default: []].insert(tag.id)
        }

        // (2) media 携带的 tag
        var mediaIds = Set<Int>()
        for items in mediaByMsg.values {
            for m in items { mediaIds.insert(m.id) }
        }
        if !mediaIds.isEmpty {
            let mediaTagSQL = """
                SELECT mtm.message_id, mt.media_id, t.id, t.name, t.category
                FROM message_media mtm
                JOIN media_tag mt ON mt.media_id = mtm.media_id
                JOIN tag t ON t.id = mt.tag_id
                WHERE mtm.message_id IN (\(placeholders))
                """
            let rows = try Row.fetchAll(
                db, sql: mediaTagSQL,
                arguments: StatementArguments(messageIds.map { $0 as DatabaseValueConvertible })
            )
            for row in rows {
                let msgId: Int = row["message_id"]
                let tag = MessageTag(id: row["id"], name: row["name"], category: row["category"])
                var seen = seenByMsg[msgId] ?? []
                if !seen.contains(tag.id) {
                    result[msgId, default: []].append(tag)
                    seen.insert(tag.id)
                }
                seenByMsg[msgId] = seen
            }
            // mediaIds 仅作为「需要查 media_tag」的判断,这里已用过
        }

        return result
    }

    // MARK: - 批量预取:media tag(给 media items 注入 tags)

    private static func fetchTagsByMedia(db: Database, mediaIds: [Int]) throws -> [Int: [MessageTag]] {
        guard !mediaIds.isEmpty else { return [:] }
        let placeholders = Array(repeating: "?", count: mediaIds.count).joined(separator: ",")
        let sql = """
            SELECT mt.media_id, t.id, t.name, t.category
            FROM media_tag mt
            JOIN tag t ON t.id = mt.tag_id
            WHERE mt.media_id IN (\(placeholders))
            """
        let rows = try Row.fetchAll(db, sql: sql, arguments: StatementArguments(mediaIds.map { $0 as DatabaseValueConvertible }))
        var out: [Int: [MessageTag]] = [:]
        for row in rows {
            let mediaId: Int = row["media_id"]
            let tag = MessageTag(id: row["id"], name: row["name"], category: row["category"])
            out[mediaId, default: []].append(tag)
        }
        return out
    }

    // MARK: - 批量预取:tag with count(给 FilterSidebar)

    private static func fetchTagsWithCount(db: Database) throws -> [Tag] {
        let sql = """
            SELECT t.id, t.name, t.category, COUNT(DISTINCT mt.message_id) AS message_count
            FROM tag t
            LEFT JOIN message_tag mt ON mt.tag_id = t.id
            GROUP BY t.id
            ORDER BY message_count DESC, t.name ASC
            """
        let rows = try Row.fetchAll(db, sql: sql)
        return rows.map { row in
            Tag(
                id: row["id"],
                name: row["name"],
                category: row["category"],
                messageCount: row["message_count"]
            )
        }
    }

    // MARK: - Issues(进行中)

    private static func fetchDoingIssues(db: Database) throws -> [Issue] {
        let sql = """
            SELECT id, title, created_at
            FROM issue
            WHERE status = 'doing'
            ORDER BY created_at DESC
            """
        let rows = try Row.fetchAll(db, sql: sql)
        return rows.map { row in
            Issue(
                id: row["id"],
                title: row["title"],
                createdAt: row["created_at"]
            )
        }
    }
}

// MARK: - 游标

/// ISO 字符串游标 —— 消息域的 cursor 直接是 `created_at` 的 ISO 字符串。
/// 失败抛 `RepositoryError.invalidCursor`,让 UI 层用 toast 提示。
enum MessageCursor {
    static let formatter = MessageISO.formatter

    static func encode(_ date: Date) -> String {
        formatter.string(from: date)
    }

    static func decode(_ raw: String) throws -> Date {
        guard let d = formatter.date(from: raw) else {
            throw RepositoryError.invalidCursor(raw)
        }
        return d
    }
}

// MARK: - 辅助类型
// (旧的 DayCount struct 已删除 —— 直接复用 Models.swift 的 TimelineEntry)
