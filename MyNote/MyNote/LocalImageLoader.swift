//
//  LocalImageLoader.swift
//  MyNote
//
//  本地缩略图异步加载 + 内存缓存。避免 AsyncImage 在大网格滚动时反复解码 webp。
//
//  缓存 key 命名空间:
//    actor 与 media 共用同一个 NSCache,但靠 `ImageKind` 枚举隔离 key,
//    避免 actorId == 42 与 mediaId == 42 互相覆盖。key 形如 "media-42" / "actor-7"。
//

import AppKit

/// NSCache key 的命名空间 —— 区分媒体缩略图与演员头像,避免 id 撞车。
enum ImageKind: String {
    case mediaThumbnail = "media"
    case actorAvatar = "actor"
}

actor LocalImageLoader {
    static let shared = LocalImageLoader()

    /// 共享 NSCache,key 走字符串 "kind-id" 格式,actor / media 互不覆盖。
    private let cache: NSCache<NSString, NSImage> = {
        let c = NSCache<NSString, NSImage>()
        c.countLimit = 500
        return c
    }()

    private init() {}

    // MARK: - 媒体缩略图

    /// 加载 mediaId 对应的 NSImage,优先从 NSCache 命中。
    /// 文件不存在或解码失败时返回 nil(由 UI 显示占位)。
    func load(mediaId: Int, url: URL) async -> NSImage? {
        await load(kind: .mediaThumbnail, id: mediaId, url: url)
    }

    /// 只读命中缓存,不发起加载。用于详情视图先垫缩略图、再异步上大图。
    func cached(mediaId: Int) -> NSImage? {
        cache.object(forKey: cacheKey(.mediaThumbnail, id: mediaId))
    }

    // MARK: - 演员头像

    /// 加载 actorId 对应的 NSImage(头像)。文件不存在 / DATA_ROOT 未配置 /
    /// 解码失败都返回 nil(由 UI 走 person.circle 占位)。
    func loadActorAvatar(actorId: Int, url: URL) async -> NSImage? {
        await load(kind: .actorAvatar, id: actorId, url: url)
    }

    // MARK: - 内部

    private func load(kind: ImageKind, id: Int, url: URL) async -> NSImage? {
        let key = cacheKey(kind, id: id)
        if let cached = cache.object(forKey: key) {
            return cached
        }
        let image: NSImage? = await Task.detached(priority: .userInitiated) {
            guard FileManager.default.fileExists(atPath: url.path) else { return nil }
            return NSImage(contentsOf: url)
        }.value

        if let image {
            cache.setObject(image, forKey: key)
        }
        return image
    }

    private func cacheKey(_ kind: ImageKind, id: Int) -> NSString {
        "\(kind.rawValue)-\(id)" as NSString
    }
}
