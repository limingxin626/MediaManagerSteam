//
//  LocalImageLoader.swift
//  MyNote
//
//  本地缩略图异步加载 + 内存缓存。避免 AsyncImage 在大网格滚动时反复解码 webp。
//

import AppKit

actor LocalImageLoader {
    static let shared = LocalImageLoader()

    private let cache: NSCache<NSNumber, NSImage> = {
        let c = NSCache<NSNumber, NSImage>()
        c.countLimit = 500
        return c
    }()

    private init() {}

    /// 加载 mediaId 对应的 NSImage,优先从 NSCache 命中。
    /// 文件不存在或解码失败时返回 nil(由 UI 显示占位)。
    func load(mediaId: Int, url: URL) async -> NSImage? {
        let key = NSNumber(value: mediaId)
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
}
