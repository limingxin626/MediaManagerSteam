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

    /// 原始媒体文件本地 URL: `{DATA_ROOT}/{file_path}`。
    /// file_path 在 backend 里是相对路径(如 `uploads/2026/06/04/xxx.mp4`)。
    var localFileURL: URL? {
        guard let root = Settings.dataRoot else { return nil }
        return root.appendingPathComponent(filePath)
    }
}
