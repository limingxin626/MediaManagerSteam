//
//  MediaLibraryViewModel.swift
//  MyNote
//
//  媒体库数据模型 - 通过 MediaSource 协议获取数据,默认本地 SQLite。
//

import Foundation
import Combine

@MainActor
class MediaLibraryViewModel: ObservableObject {
    @Published var media: [Media] = []
    @Published var isLoading = false
    @Published var isLoadingMore = false
    @Published var errorMessage: String? = nil
    @Published var nextCursor: String? = nil
    @Published var hasMore = false
    @Published var selectedMediaType: String? = nil  // nil (全部), "image", "video"
    @Published var showOnlyStarred = false

    private let mediaSource: MediaSource

    init(mediaSource: MediaSource = LocalMediaSource()) {
        self.mediaSource = mediaSource
    }

    // MARK: - 加载

    /// 加载第一页(替换已有数据)。
    func loadInitial() async {
        isLoading = true
        errorMessage = nil
        defer { isLoading = false }

        do {
            let response = try await mediaSource.list(
                cursor: nil,
                limit: 40,
                type: selectedMediaType,
                starredOnly: showOnlyStarred
            )
            media = response.items
            nextCursor = response.nextCursor
            hasMore = response.hasMore
        } catch {
            errorMessage = error.localizedDescription
        }
    }

    /// 加载下一页(append)。
    func loadMore() async {
        guard !isLoadingMore, hasMore, nextCursor != nil else { return }

        isLoadingMore = true
        defer { isLoadingMore = false }

        do {
            let response = try await mediaSource.list(
                cursor: nextCursor,
                limit: 40,
                type: selectedMediaType,
                starredOnly: showOnlyStarred
            )
            media.append(contentsOf: response.items)
            nextCursor = response.nextCursor
            hasMore = response.hasMore
        } catch {
            errorMessage = error.localizedDescription
        }
    }

    /// 下拉刷新,等同 loadInitial。
    func refresh() async {
        await loadInitial()
    }

    // MARK: - 过滤

    func changeMediaType(_ type: String?) async {
        selectedMediaType = type
        await loadInitial()
    }

    func toggleStarredOnly() async {
        showOnlyStarred.toggle()
        await loadInitial()
    }
}
