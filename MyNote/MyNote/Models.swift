//
//  Models.swift
//  MyNote
//
//  API 数据模型，与后端 Pydantic schemas 对应
//

import Foundation

// MARK: - Message 相关

struct Message: Identifiable, Codable {
    let id: Int
    let text: String?
    let createdAt: String
    let updatedAt: String?
    let actorId: Int?
    let actorName: String?
    let issueId: Int?
    let issueTitle: String?
    let mediaCount: Int
    let starred: Bool
    
    let mediaItems: [MessageMediaItem]
    let tags: [MessageTag]
    
    enum CodingKeys: String, CodingKey {
        case id, text
        case createdAt = "created_at"
        case updatedAt = "updated_at"
        case actorId = "actor_id"
        case actorName = "actor_name"
        case issueId = "issue_id"
        case issueTitle = "issue_title"
        case mediaCount = "media_count"
        case starred
        case mediaItems = "media_items"
        case tags
    }
}

struct MessageMediaItem: Identifiable, Codable {
    let id: Int
    let filePath: String
    let fileUrl: String
    let thumbPath: String
    let thumbUrl: String
    let mimeType: String?
    let width: Int?
    let height: Int?
    let durationMs: Int?
    let starred: Bool
    let createdAt: String
    let updatedAt: String
    
    let tags: [MessageTag]
    
    enum CodingKeys: String, CodingKey {
        case id
        case filePath = "file_path"
        case fileUrl = "file_url"
        case thumbPath = "thumb_path"
        case thumbUrl = "thumb_url"
        case mimeType = "mime_type"
        case width, height
        case durationMs = "duration_ms"
        case starred
        case createdAt = "created_at"
        case updatedAt = "updated_at"
        case tags
    }
}

// MARK: - Tag 相关

struct MessageTag: Identifiable, Codable {
    let id: Int
    let name: String
    let category: String?
}

// MARK: - 分页响应

struct MessageCursorResponse: Codable {
    let items: [Message]
    let nextCursor: String?
    let prevCursor: String?
    let hasMore: Bool
    let hasMoreBefore: Bool
    
    enum CodingKeys: String, CodingKey {
        case items
        case nextCursor = "next_cursor"
        case prevCursor = "prev_cursor"
        case hasMore = "has_more"
        case hasMoreBefore = "has_more_before"
    }
}

// MARK: - Media 相关

struct Media: Identifiable, Codable {
    let id: Int
    let filePath: String
    let repoId: String?
    let fileUrl: String
    let thumbPath: String
    let thumbUrl: String
    let fileSize: Int?
    let mimeType: String?
    let width: Int?
    let height: Int?
    let durationMs: Int?
    let rating: Int
    let starred: Bool
    let viewCount: Int
    let tags: [MessageTag]
    let videoMediaId: Int?
    let frameMs: Int?
    let startMs: Int?
    let endMs: Int?
    let takenAt: String?
    let gpsLat: Double?
    let gpsLng: Double?
    let orientation: Int?
    let cameraMake: String?
    let cameraModel: String?
    let lens: String?
    let videoCodec: String?
    let audioCodec: String?
    let hasAudio: Int?
    let fps: Double?
    let bitrate: Int?
    let createdAt: String
    let updatedAt: String
    
    enum CodingKeys: String, CodingKey {
        case id
        case filePath = "file_path"
        case repoId = "repo_id"
        case fileUrl = "file_url"
        case thumbPath = "thumb_path"
        case thumbUrl = "thumb_url"
        case fileSize = "file_size"
        case mimeType = "mime_type"
        case width, height
        case durationMs = "duration_ms"
        case rating
        case starred
        case viewCount = "view_count"
        case tags
        case videoMediaId = "video_media_id"
        case frameMs = "frame_ms"
        case startMs = "start_ms"
        case endMs = "end_ms"
        case takenAt = "taken_at"
        case gpsLat = "gps_lat"
        case gpsLng = "gps_lng"
        case orientation
        case cameraMake = "camera_make"
        case cameraModel = "camera_model"
        case lens
        case videoCodec = "video_codec"
        case audioCodec = "audio_codec"
        case hasAudio = "has_audio"
        case fps
        case bitrate
        case createdAt = "created_at"
        case updatedAt = "updated_at"
    }
}

// MARK: - 时间线条目

/// 按日期分组的媒体统计,与 backend /media/timeline 对齐。
struct TimelineEntry: Identifiable, Codable {
    let year: Int
    let month: Int
    let day: Int
    let count: Int

    /// 唯一标识(同一天不会重复)。
    var id: String { "\(year)-\(month)-\(day)" }

    /// 该条目对应的 Date(天级别,时间部分为午夜)。
    var date: Date {
        var comp = DateComponents()
        comp.year = year
        comp.month = month
        comp.day = day
        return Calendar.current.date(from: comp) ?? Date()
    }

    enum CodingKeys: String, CodingKey {
        case year, month, day, count
    }
}

// MARK: - Media 分页响应

struct MediaCursorResponse: Codable {
    let items: [Media]
    let nextCursor: String?
    let prevCursor: String?
    let hasMore: Bool
    let hasMoreBefore: Bool
    
    enum CodingKeys: String, CodingKey {
        case items
        case nextCursor = "next_cursor"
        case prevCursor = "prev_cursor"
        case hasMore = "has_more"
        case hasMoreBefore = "has_more_before"
    }
}

// MARK: - 错误响应

struct ErrorResponse: Codable {
    let detail: String
}

// MARK: - Media 本地路径扩展

extension Media {
    /// 缩略图本地 URL: `{DATA_ROOT}/data/thumbs/{id}.webp`。
    /// DATA_ROOT 未配置时返回 nil。
    var localThumbURL: URL? {
        guard let root = Settings.dataRoot else { return nil }
        return root
            .appendingPathComponent("data", isDirectory: true)
            .appendingPathComponent("thumbs", isDirectory: true)
            .appendingPathComponent("\(id).webp")
    }

    /// 原始媒体文件本地 URL。
    ///
    /// 2026/06 起,backend 把 `file_path` 改成「相对挂载根的 forward-slash 相对路径」,
    /// `repo_id` 标识它挂在哪个 repo 上。这里通过 `RepositoryManager` 拼回本机绝对 URL。
    ///
    /// Repo 不可用时(外接盘没插)仍会返回 URL —— 文件不存在交由 `FileManager` 检测,
    /// UI 走 `isRepoAvailable` 分支显示「请插入 XX 硬盘」。
    ///
    /// 老数据兜底:`repoId == nil`(读到迁移前 DB)或 repo 未注册 → 走 `legacyExtractedURL()`
    /// 的字符串抠子串逻辑,行为退化到迁移前。
    @MainActor
    var localFileURL: URL? {
        if let url = RepositoryManager.shared.resolve(repoId: repoId, relativePath: filePath) {
            return url
        }
        return legacyExtractedURL()
    }

    /// 该 media 所在 repo 是否当前可用。UI 用来决定是否显示「请插入 XX 硬盘」。
    /// 老数据(repoId == nil)按 dataRoot 是否配好兜底。
    @MainActor
    var isRepoAvailable: Bool {
        if repoId != nil {
            return RepositoryManager.shared.isAvailable(repoId: repoId)
        }
        return Settings.dataRoot != nil
    }

    /// UI 显示用的 repo 名(humanName ?? repoId ?? "default")。
    @MainActor
    var repoDisplayName: String {
        RepositoryManager.shared.displayName(repoId: repoId)
    }

    /// 老路径(迁移前数据 / 未知 repo)的兜底逻辑。沿用迁移前的字符串抠子串方案,
    /// 默认拼到 `Settings.dataRoot` 之下。仅用于历史兼容。
    private func legacyExtractedURL() -> URL? {
        guard let root = Settings.dataRoot else { return nil }
        let normalized = filePath.replacingOccurrences(of: "\\", with: "/")

        // 找 "/uploads/" 或开头的 "uploads/" 两种形式都接受。
        let marker = "/uploads/"
        let relativePart: String
        if let range = normalized.range(of: marker) {
            relativePart = String(normalized[range.lowerBound...])
                .trimmingCharacters(in: CharacterSet(charactersIn: "/"))
        } else if normalized.hasPrefix("uploads/") {
            relativePart = normalized
        } else {
            relativePart = normalized
        }

        return root.appendingPathComponent(relativePart)
    }
}
