//
//  MediaRecord.swift
//  MyNote
//
//  GRDB 映射 `media` 表,字段与 backend/app/models/__init__.py 的 Media 一一对齐。
//

import Foundation
import GRDB

struct MediaRecord: Codable, FetchableRecord, TableRecord {
    static let databaseTableName = "media"

    let id: Int
    let filePath: String
    let repoId: String?
    let fileHash: String?
    let fileSize: Int?
    let mimeType: String?
    let width: Int?
    let height: Int?
    let durationMs: Int?

    let takenAt: Date?
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

    let rating: Int
    let starred: Int
    let viewCount: Int
    let lastViewedAt: Date?
    let createdAt: Date
    let updatedAt: Date

    let videoMediaId: Int?
    let frameMs: Int?
    let startMs: Int?
    let endMs: Int?

    enum CodingKeys: String, CodingKey {
        case id
        case filePath = "file_path"
        case repoId = "repo_id"
        case fileHash = "file_hash"
        case fileSize = "file_size"
        case mimeType = "mime_type"
        case width
        case height
        case durationMs = "duration_ms"
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
        case rating
        case starred
        case viewCount = "view_count"
        case lastViewedAt = "last_viewed_at"
        case createdAt = "created_at"
        case updatedAt = "updated_at"
        case videoMediaId = "video_media_id"
        case frameMs = "frame_ms"
        case startMs = "start_ms"
        case endMs = "end_ms"
    }
}

extension MediaRecord {
    /// 转成 UI 层用的 `Media`(`Models.swift` 已定义)。
    /// tags 由 repository 批量取出后注入,避免 N+1。
    func toUIModel(tags: [MessageTag]) -> Media {
        let isoFormatter = ISO8601DateFormatter()
        isoFormatter.formatOptions = [.withInternetDateTime, .withFractionalSeconds]

        func iso(_ date: Date) -> String {
            isoFormatter.string(from: date)
        }
        func isoOpt(_ date: Date?) -> String? {
            date.map { isoFormatter.string(from: $0) }
        }

        // file_url / thumb_url 仍保留(沿用 backend 的 path 约定),
        // 但 UI 优先用 localFileURL / localThumbURL 计算属性(见 Models.swift 扩展)。
        let fileUrl = "/data/\(filePath)"
        let thumbPath = "data/thumbs/\(id).webp"
        let thumbUrl = "/data/thumbs/\(id).webp"

        return Media(
            id: id,
            filePath: filePath,
            repoId: repoId,
            fileUrl: fileUrl,
            thumbPath: thumbPath,
            thumbUrl: thumbUrl,
            fileSize: fileSize,
            mimeType: mimeType,
            width: width,
            height: height,
            durationMs: durationMs,
            rating: rating,
            starred: starred != 0,
            viewCount: viewCount,
            tags: tags,
            videoMediaId: videoMediaId,
            frameMs: frameMs,
            startMs: startMs,
            endMs: endMs,
            takenAt: isoOpt(takenAt),
            gpsLat: gpsLat,
            gpsLng: gpsLng,
            orientation: orientation,
            cameraMake: cameraMake,
            cameraModel: cameraModel,
            lens: lens,
            videoCodec: videoCodec,
            audioCodec: audioCodec,
            hasAudio: hasAudio,
            fps: fps,
            bitrate: bitrate,
            createdAt: iso(createdAt),
            updatedAt: iso(updatedAt)
        )
    }
}
