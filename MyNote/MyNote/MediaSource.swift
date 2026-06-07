//
//  MediaSource.swift
//  MyNote
//
//  ViewModel 与数据来源之间的契约。默认 LocalMediaSource(本地 SQLite);
//  APIMediaSource 包装现有 APIClient,作为调试/回退路径保留。
//

import Foundation

protocol MediaSource {
    func list(
        cursor: String?,
        limit: Int,
        type: String?,
        starredOnly: Bool
    ) async throws -> MediaCursorResponse

    /// 时间线:按日期分组统计媒体数量。
    func timeline(
        type: String?,
        starredOnly: Bool
    ) async throws -> [TimelineEntry]
}

// MARK: - Local

final class LocalMediaSource: MediaSource {
    private let repository: MediaRepository

    init(repository: MediaRepository = MediaRepository()) {
        self.repository = repository
    }

    func list(
        cursor: String?,
        limit: Int,
        type: String?,
        starredOnly: Bool
    ) async throws -> MediaCursorResponse {
        let result = try await repository.list(
            cursor: cursor,
            limit: limit,
            type: type,
            starredOnly: starredOnly
        )
        return MediaCursorResponse(
            items: result.items,
            nextCursor: result.nextCursor,
            prevCursor: nil,
            hasMore: result.hasMore,
            hasMoreBefore: false
        )
    }

    func timeline(
        type: String?,
        starredOnly: Bool
    ) async throws -> [TimelineEntry] {
        try await repository.timeline(type: type, starredOnly: starredOnly)
    }
}

// MARK: - API (回退/调试)

final class APIMediaSource: MediaSource {
    private let apiClient: APIClient

    init(apiClient: APIClient = APIClient()) {
        self.apiClient = apiClient
    }

    func list(
        cursor: String?,
        limit: Int,
        type: String?,
        starredOnly: Bool
    ) async throws -> MediaCursorResponse {
        try await apiClient.getMedia(
            cursor: cursor,
            limit: limit,
            type: type,
            starred: starredOnly ? true : nil
        )
    }

    func timeline(
        type: String?,
        starredOnly: Bool
    ) async throws -> [TimelineEntry] {
        try await apiClient.getMediaTimeline(
            type: type,
            starred: starredOnly ? true : nil
        )
    }
}
