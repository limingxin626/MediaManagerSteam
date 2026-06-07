//
//  MediaLibraryViewModel.swift
//  MyNote
//
//  媒体库数据模型 - 通过 MediaSource 协议获取数据,默认本地 SQLite。
//

import Foundation
import Combine

/// 日期桶:同一天的媒体为一组,含该天首条媒体的 created_at 用于排序。
struct MediaDateBucket: Identifiable {
    let year: Int
    let month: Int
    let day: Int
    var items: [Media]

    var id: String { "\(year)-\(month)-\(day)" }
    var date: Date {
        var comp = DateComponents()
        comp.year = year
        comp.month = month
        comp.day = day
        return Calendar.current.date(from: comp) ?? Date()
    }
    var headerText: String {
        let formatter = DateFormatter()
        formatter.dateFormat = "yyyy年M月d日"
        return formatter.string(from: date)
    }
}

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

    // 时间线
    @Published var timeline: [TimelineEntry] = []
    @Published var buckets: [MediaDateBucket] = []
    /// Scrubber 指示器对应的当前日期(滚动时跟着视口最顶部日期桶变化)。
    @Published var currentDate: Date = Date()

    private let mediaSource: MediaSource

    init(mediaSource: MediaSource = LocalMediaSource()) {
        self.mediaSource = mediaSource
    }

    // MARK: - 加载

    /// 加载时间线(用于 DateScrubber)。
    func loadTimeline() async {
        do {
            timeline = try await mediaSource.timeline(
                type: selectedMediaType,
                starredOnly: showOnlyStarred
            )
        } catch {
            // 时间线失败不影响媒体加载
            print("Timeline load error: \(error)")
        }
    }

    /// 加载第一页(替换已有数据)。
    func loadInitial() async {
        isLoading = true
        errorMessage = nil
        defer { isLoading = false }

        do {
            let response = try await mediaSource.list(
                cursor: nil,
                limit: 200,
                type: selectedMediaType,
                starredOnly: showOnlyStarred
            )
            media = response.items
            nextCursor = response.nextCursor
            hasMore = response.hasMore
            rebuildBuckets()
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
                limit: 200,
                type: selectedMediaType,
                starredOnly: showOnlyStarred
            )
            media.append(contentsOf: response.items)
            nextCursor = response.nextCursor
            hasMore = response.hasMore
            rebuildBuckets()
        } catch {
            errorMessage = error.localizedDescription
        }
    }

    /// 下拉刷新,等同 loadInitial。
    func refresh() async {
        await loadInitial()
    }

    // MARK: - 日期桶

    /// 根据当前 media 数组按日期分组构建 buckets。
    /// 每个桶内 items 按原本的 created_at DESC 排列。
    private func rebuildBuckets() {
        let formatter = ISO8601DateFormatter()
        formatter.formatOptions = [.withInternetDateTime, .withFractionalSeconds]

        var bucketMap: [String: MediaDateBucket] = [:]

        for media in media {
            guard let createdAt = formatter.date(from: media.createdAt) else { continue }
            let components = Calendar.current.dateComponents([.year, .month, .day], from: createdAt)
            guard let year = components.year, let month = components.month, let day = components.day else { continue }
            let key = "\(year)-\(month)-\(day)"

            if var bucket = bucketMap[key] {
                bucket.items.append(media)
                bucketMap[key] = bucket
            } else {
                bucketMap[key] = MediaDateBucket(year: year, month: month, day: day, items: [media])
            }
        }

        // 按日期倒序(最新在前)
        buckets = bucketMap.values.sorted {
            if $0.year != $1.year { return $0.year > $1.year }
            if $0.month != $1.month { return $0.month > $1.month }
            return $0.day > $1.day
        }
    }

    /// 滚动到指定日期桶(供 DateScrubber 跳转用)。
    func scrollToDate(_ date: Date) {
        currentDate = date
        let components = Calendar.current.dateComponents([.year, .month, .day], from: date)
        guard let year = components.year, let month = components.month, let day = components.day else { return }
        let key = "\(year)-\(month)-\(day)"
        // 通知 View 层滚动 — View 通过 @Published buckets 变化自行定位
        if let idx = buckets.firstIndex(where: { $0.id == key }) {
            // 广播当前选中桶索引(供 View 滚动定位)
            _scrollToBucketIndex = idx
        }
    }

    /// 内部:滚动到桶索引(由 View 消费)。
    @Published var _scrollToBucketIndex: Int? = nil

    // MARK: - 过滤

    func changeMediaType(_ type: String?) async {
        selectedMediaType = type
        await loadTimeline()
        await loadInitial()
    }

    func toggleStarredOnly() async {
        showOnlyStarred.toggle()
        await loadTimeline()
        await loadInitial()
    }
}
