//
//  MediaRepository.swift
//  MyNote
//
//  数据访问层 - 媒体网格分页查询 + 标签批量加载。
//

import Foundation
import GRDB

enum RepositoryError: LocalizedError {
    case databaseNotOpen
    case invalidCursor(String)

    var errorDescription: String? {
        switch self {
        case .databaseNotOpen:
            return "数据库未连接"
        case .invalidCursor(let raw):
            return "无效的分页游标: \(raw)"
        }
    }
}

/// 复合游标格式:`"{createdAtIsoMs}|{id}"`
/// 例如 `"2026-06-04T19:25:51.000|1234"`。
private enum MediaCursor {
    /// 用 SQLite 实际存储的 ISO 字符串(GRDB 默认格式)做比较,避免时区漂移。
    static let formatter: ISO8601DateFormatter = {
        let f = ISO8601DateFormatter()
        f.formatOptions = [.withInternetDateTime, .withFractionalSeconds]
        return f
    }()

    static func encode(createdAt: Date, id: Int) -> String {
        "\(formatter.string(from: createdAt))|\(id)"
    }

    static func decode(_ raw: String) throws -> (createdAt: Date, id: Int) {
        let parts = raw.split(separator: "|", maxSplits: 1, omittingEmptySubsequences: false)
        guard parts.count == 2,
              let date = formatter.date(from: String(parts[0])),
              let id = Int(parts[1])
        else {
            throw RepositoryError.invalidCursor(raw)
        }
        return (date, id)
    }
}

final class MediaRepository {
    private let database: LocalDatabase

    init(database: LocalDatabase = .shared) {
        self.database = database
    }

    /// 时间线:按日期分组统计媒体数量(最新日期在前)。
    /// 返回 [(year, month, day, count)],仅包含有媒体的日期。
    func timeline(
        type: String?,
        starredOnly: Bool
    ) async throws -> [TimelineEntry] {
        guard let queue = database.queue else { throw RepositoryError.databaseNotOpen }

        return try await queue.read { db -> [TimelineEntry] in
            var where_: [String] = []
            var args: [DatabaseValueConvertible] = []

            // 排除子媒体(章节/帧)
            where_.append("video_media_id IS NULL")

            if let type = type {
                switch type {
                case "image":
                    where_.append("mime_type LIKE 'image/%'")
                case "video":
                    where_.append("mime_type LIKE 'video/%'")
                default:
                    break
                }
            }
            if starredOnly {
                where_.append("starred = 1")
            }

            let whereClause = where_.isEmpty ? "" : "WHERE \(where_.joined(separator: " AND "))"

            let sql = """
                SELECT
                    CAST(strftime('%Y', created_at) AS INTEGER) AS year,
                    CAST(strftime('%m', created_at) AS INTEGER) AS month,
                    CAST(strftime('%d', created_at) AS INTEGER) AS day,
                    COUNT(*) AS count
                FROM media
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

    /// 取一页 Media + 关联 tags。
    /// 排序按 `created_at DESC, id DESC`,符合"最新优先"。
    func list(
        cursor: String?,
        limit: Int,
        type: String?,
        starredOnly: Bool
    ) async throws -> (items: [Media], nextCursor: String?, hasMore: Bool) {
        guard let queue = database.queue else { throw RepositoryError.databaseNotOpen }

        // cursor 校验提前抛出,避免后台线程吃掉
        let cursorTuple: (Date, Int)? = try cursor.map { try MediaCursor.decode($0) }

        return try await queue.read { db -> (items: [Media], nextCursor: String?, hasMore: Bool) in
            var where_: [String] = []
            var args: [DatabaseValueConvertible] = []

            if let (cDate, cId) = cursorTuple {
                where_.append("(created_at < ? OR (created_at = ? AND id < ?))")
                args.append(cDate)
                args.append(cDate)
                args.append(cId)
            }
            if let type = type {
                switch type {
                case "image":
                    where_.append("mime_type LIKE 'image/%'")
                case "video":
                    where_.append("mime_type LIKE 'video/%'")
                default:
                    break
                }
            }
            if starredOnly {
                where_.append("starred = 1")
            }

            let whereClause = where_.isEmpty ? "" : "WHERE \(where_.joined(separator: " AND "))"
            let sql = """
                SELECT * FROM media
                \(whereClause)
                ORDER BY created_at DESC, id DESC
                LIMIT ?
                """
            var allArgs = args
            allArgs.append(limit + 1)

            let rows = try MediaRecord.fetchAll(db, sql: sql, arguments: StatementArguments(allArgs))

            let hasMore = rows.count > limit
            let page = hasMore ? Array(rows.prefix(limit)) : rows
            let nextCursor: String? = {
                guard hasMore, let last = page.last else { return nil }
                return MediaCursor.encode(createdAt: last.createdAt, id: last.id)
            }()

            // 批量取 tags,避免 N+1
            let ids = page.map { $0.id }
            let tagsByMedia = try Self.fetchTags(db: db, mediaIds: ids)
            let items = page.map { $0.toUIModel(tags: tagsByMedia[$0.id] ?? []) }

            return (items, nextCursor, hasMore)
        }
    }

    /// 单条 SQL 取出一批 media 的所有标签关联。
    private static func fetchTags(db: Database, mediaIds: [Int]) throws -> [Int: [MessageTag]] {
        guard !mediaIds.isEmpty else { return [:] }

        let placeholders = Array(repeating: "?", count: mediaIds.count).joined(separator: ",")
        let sql = """
            SELECT mt.media_id, t.id, t.name, t.category
            FROM media_tag mt
            JOIN tag t ON t.id = mt.tag_id
            WHERE mt.media_id IN (\(placeholders))
            """
        let rows = try Row.fetchAll(db, sql: sql, arguments: StatementArguments(mediaIds.map { $0 as DatabaseValueConvertible }))

        var result: [Int: [MessageTag]] = [:]
        for row in rows {
            let mediaId: Int = row["media_id"]
            let tag = MessageTag(
                id: row["id"],
                name: row["name"],
                category: row["category"]
            )
            result[mediaId, default: []].append(tag)
        }
        return result
    }
}
