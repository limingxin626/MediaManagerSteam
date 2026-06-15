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
    let repoId: String?
    let filePath: String
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
        case repoId = "repo_id"
        case filePath = "file_path"
        case mimeType = "mime_type"
        case width, height
        case durationMs = "duration_ms"
        case starred
        case createdAt = "created_at"
        case updatedAt = "updated_at"
        case tags
    }

    /// 从 `Media` UI 模型构造 —— MessageRepository 拿到 `MediaRecord` → `Media`
    /// 后,转成 `MessageMediaItem` 喂给消息视图。
    init(from media: Media) {
        self.id = media.id
        self.repoId = media.repoId
        self.filePath = media.filePath
        self.mimeType = media.mimeType
        self.width = media.width
        self.height = media.height
        self.durationMs = media.durationMs
        self.starred = media.starred
        self.createdAt = media.createdAt
        self.updatedAt = media.updatedAt
        self.tags = media.tags
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
    /// 缩略图本地 URL: `{DATA_ROOT}/thumbs/{id}.webp`。
    /// DATA_ROOT 未配置时返回 nil。
    var localThumbURL: URL? {
        guard let root = Settings.dataRoot else { return nil }
        return root
            .appendingPathComponent("thumbs", isDirectory: true)
            .appendingPathComponent("\(id).webp")
    }

    /// MP4 预览本地 URL: `{DATA_ROOT}/preview/{id}.mp4`。
    /// Backend `transcode_gif_previews.py` 把 image/gif 转成 H.264 10fps 小尺寸 MP4
    /// 放在这里,给 AnimatedVideoView 走 AVPlayer 硬件解码播。
    /// 缺失时返回 URL(不存在的文件由调用方 FileManager 检测后回退到 AnimatedImageView)。
    var localPreviewURL: URL? {
        guard let root = Settings.dataRoot else { return nil }
        return root
            .appendingPathComponent("preview", isDirectory: true)
            .appendingPathComponent("\(id).mp4")
    }

    /// 原始媒体文件本地 URL。
    ///
    /// `RepositoryManager.resolve(repoId:, relativePath:)` 是唯一来源。
    /// repo 未注册(老 `__legacy__` 数据)或当前平台未配置 darwin path → 返回 nil。
    /// 外接盘没插的情况返回 URL,文件存在性由调用方 `FileManager` 检测,
    /// UI 走 `isRepoAvailable` 分支显示「请插入 XX 硬盘」。
    @MainActor
    var localFileURL: URL? {
        RepositoryManager.shared.resolve(repoId: repoId, relativePath: filePath)
    }

    /// 该 media 所在 repo 是否当前可用。UI 用来决定是否显示「请插入 XX 硬盘」。
    @MainActor
    var isRepoAvailable: Bool {
        RepositoryManager.shared.isAvailable(repoId: repoId)
    }

    /// UI 显示用的 repo 名(humanName ?? repoId ?? "default")。
    @MainActor
    var repoDisplayName: String {
        RepositoryManager.shared.displayName(repoId: repoId)
    }
}

// MARK: - MessageMediaItem 本地路径

extension MessageMediaItem {
    /// 缩略图本地 URL: `{DATA_ROOT}/thumbs/{id}.webp`。
    /// 与 `Media.localThumbURL` 走同一条路径约定(GRDB 直读的 message 关联的
    /// media,缩略图文件 id 与 media.id 1:1 对应)。
    var localThumbURL: URL? {
        guard let root = Settings.dataRoot else { return nil }
        return root
            .appendingPathComponent("thumbs", isDirectory: true)
            .appendingPathComponent("\(id).webp")
    }

    /// 原始媒体文件本地 URL —— 经 `RepositoryManager` 解析 repoId + filePath。
    /// repo 未注册 / 未配 darwin path → 返回 nil。
    @MainActor
    var localFileURL: URL? {
        RepositoryManager.shared.resolve(repoId: repoId, relativePath: filePath)
    }

    /// 所在 repo 是否当前可用。UI 用以决定显示「请插入 XX 硬盘」占位。
    @MainActor
    var isRepoAvailable: Bool {
        RepositoryManager.shared.isAvailable(repoId: repoId)
    }
}

// MARK: - 过滤侧栏 UI 模型

/// 标签侧栏条目 —— 在 `MessageTag` 基础上加消息数字段(FilterSidebar 排序用)。
struct Tag: Identifiable, Codable, Equatable {
    let id: Int
    let name: String
    let category: String?
    let messageCount: Int
}

/// 演员侧栏条目 —— 来自 `Actor` 简化版 GRDB 映射,FilterSidebar 渲染所需。
struct Actor: Identifiable, Codable, Equatable {
    let id: Int
    let name: String
    let avatarPath: String?
    let messageCount: Int

    /// 演员头像本地 URL: `{DATA_ROOT}/actor_cover/{id}.webp`。
    /// 缺失时返回 nil(老数据未生成头像 / DATA_ROOT 未配置),UI 走 person.circle 占位。
    var localAvatarURL: URL? {
        guard let root = Settings.dataRoot else { return nil }
        return root
            .appendingPathComponent("actor_cover", isDirectory: true)
            .appendingPathComponent("\(id).webp")
    }
}

/// Issue 侧栏条目 —— 简化为列表与过滤所需字段。
struct Issue: Identifiable, Codable, Equatable {
    let id: Int
    let title: String
    let createdAt: Date
}
