//
//  MessageRecord.swift
//  MyNote
//
//  GRDB 映射 message / message_media / actor / tag 四张表,与 backend
//  app/models/__init__.py 的 SQLAlchemy schema 一一对应。
//
//  风格对齐 MediaRecord:snake_case 列名 → camelCase 字段,CodingKeys 显式声明。
//  record 与 UI 模型(Models.swift 里的 Message / MessageMediaItem / Actor /
//  MessageTag)解耦:本文件只负责 SQL 反序列化,UI 字段类型(String? / Bool / ...)
//  由 toUIModel() 转换。
//

import Foundation
import GRDB

// MARK: - MessageRecord

struct MessageRecord: Codable, FetchableRecord, TableRecord {
    static let databaseTableName = "message"

    let id: Int
    let text: String?
    let actorId: Int?
    let issueId: Int?
    let starred: Int
    let createdAt: Date
    let updatedAt: Date

    enum CodingKeys: String, CodingKey {
        case id
        case text
        case actorId = "actor_id"
        case issueId = "issue_id"
        case starred
        case createdAt = "created_at"
        case updatedAt = "updated_at"
    }
}

// MARK: - MessageMediaRecord

struct MessageMediaRecord: Codable, FetchableRecord, TableRecord {
    static let databaseTableName = "message_media"

    let id: Int
    let messageId: Int
    let mediaId: Int
    let position: Int
    let createdAt: Date

    enum CodingKeys: String, CodingKey {
        case id
        case messageId = "message_id"
        case mediaId = "media_id"
        case position
        case createdAt = "created_at"
    }
}

// MARK: - ActorRecord

struct ActorRecord: Codable, FetchableRecord, TableRecord {
    static let databaseTableName = "actor"

    let id: Int
    let name: String
    let description: String?
    let avatarPath: String?
    let createdAt: Date
    let updatedAt: Date

    enum CodingKeys: String, CodingKey {
        case id
        case name
        case description
        case avatarPath = "avatar_path"
        case createdAt = "created_at"
        case updatedAt = "updated_at"
    }
}

// MARK: - TagRecord

struct TagRecord: Codable, FetchableRecord, TableRecord {
    static let databaseTableName = "tag"

    let id: Int
    let name: String
    let category: String?

    enum CodingKeys: String, CodingKey {
        case id
        case name
        case category
    }
}

// MARK: - IssueRecord

/// 消息域的 issue 简化版,仅含列表与过滤所需字段。完整字段在 backend `Issue` 模型,
/// 本表与 issue.py schema 对齐。
struct IssueRecord: Codable, FetchableRecord, TableRecord {
    static let databaseTableName = "issue"

    let id: Int
    let title: String
    let status: String
    let position: Int
    let createdAt: Date
    let updatedAt: Date

    enum CodingKeys: String, CodingKey {
        case id
        case title
        case status
        case position
        case createdAt = "created_at"
        case updatedAt = "updated_at"
    }
}

// MARK: - 共享 ISO 工具

/// 消息域所有 ISO 时间戳走同一格式(.withInternetDateTime + .withFractionalSeconds),
/// 与 backend `datetime.isoformat()` 默认输出一致,以及 Models.swift 里
/// `Media.toUIModel` 已经在用的 ISO 行为一致。
enum MessageISO {
    static let formatter: ISO8601DateFormatter = {
        let f = ISO8601DateFormatter()
        f.formatOptions = [.withInternetDateTime, .withFractionalSeconds]
        return f
    }()

    static func format(_ date: Date) -> String {
        formatter.string(from: date)
    }

    static func formatOpt(_ date: Date?) -> String? {
        date.map { formatter.string(from: $0) }
    }
}

// MARK: - toUIModel

extension MessageRecord {
    /// 转成 UI 层用的 `Message`(Models.swift 已定义)。
    /// actor / mediaItems / tags 由 MessageRepository 批量预取后注入,本方法只
    /// 负责 record → UI 字段转换。
    func toUIModel(
        actor: ActorRecord?,
        mediaItems: [MessageMediaItem],
        tags: [MessageTag]
    ) -> Message {
        Message(
            id: id,
            text: text,
            createdAt: MessageISO.format(createdAt),
            updatedAt: MessageISO.format(updatedAt),
            actorId: actorId,
            actorName: actor?.name,
            issueId: issueId,
            // issueTitle 需要额外 JOIN —— MessageRepository 暂未批量预取 issue;
            // 这里先按 nil 输出,UI 显示「#issueId」格式占位,后续如要标题再加批量预取。
            issueTitle: nil,
            mediaCount: mediaItems.count,
            starred: starred != 0,
            mediaItems: mediaItems,
            tags: tags
        )
    }
}
