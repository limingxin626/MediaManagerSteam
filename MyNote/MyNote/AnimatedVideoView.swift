//
//  AnimatedVideoView.swift
//  MyNote
//
//  用 AVPlayer + AVPlayerLooper 播 MP4 preview(iOS 走 VideoToolbox
//  硬件解码,<5ms 冷启),AnimatedImageView 的性能替代。
//
//  来源约定:MyNote 把 GIF 转成 H.264 MP4 后放在
//  `{DATA_ROOT}/data/preview/{id}.mp4`,本 view 读这个路径播。
//  若文件不存在,调用方应回退到 AnimatedImageView(本 view 不做兜底)。
//
//  用法:
//    AnimatedVideoView(url: media.localPreviewURL!, contentMode: .fill)
//        .frame(width: 200, height: 200)
//
//  性能关键 —— `VideoPlayerPool` 按 URL 跨 cell 复用 AVPlayer / AVPlayerLayer:
//  vmc2BuildDecompressionSession(VideoToolbox 硬解 session 初始化)要 30-50ms,
//  LazyVGrid 滚动时若每个 cell 出现都新建,几十 cell 排队 = 明显卡顿。
//  pool 命中时 acquire 只是 dict 查表 + play(),<1ms。
//

import SwiftUI
import AVFoundation
import AVKit

/// 按 URL 共享的 AVPlayer 池,跨 cell 复用避免反复 create / destroy
/// VideoToolbox session(view 出现/消失不释放,只 play/pause)。
/// `NSCache` 自动 LRU + 内存压力清理,`countLimit` 控制峰值。
@MainActor
final class VideoPlayerPool {
    static let shared = VideoPlayerPool()
    private let cache = NSCache<NSURL, PlayerBundle>()

    private init() {
        // 网格(~15 cells) + 详情(1) + 一定冗余 = 30 够用。NSCache 满了会自动
        // evict 最久未访问的,内存压力下也会清理。
        cache.countLimit = 30
    }

    /// 拿 layer 并立刻 play。cache 命中时不重建 AVPlayer,只 play。
    func acquire(_ url: URL) -> AVPlayerLayer {
        if let bundle = cache.object(forKey: url as NSURL) {
            bundle.queue.play()
            return bundle.layer
        }
        let bundle = PlayerBundle(url: url)
        cache.setObject(bundle, forKey: url as NSURL)
        bundle.queue.play()
        return bundle.layer
    }

    /// view 消失时只暂停,不清缓存。NSCache 按 countLimit 自动 evict。
    func release(_ url: URL) {
        cache.object(forKey: url as NSURL)?.queue.pause()
    }

    /// 主动清空(暂未使用,留作调试 / 强制重置时调用)。
    func purgeAll() {
        cache.removeAllObjects()
    }
}

/// 不可变 bundle:queue / looper / layer 一起创建,一起释放,绑死同一个 url。
private final class PlayerBundle {
    let queue: AVQueuePlayer
    let looper: AVPlayerLooper
    let layer: AVPlayerLayer

    init(url: URL) {
        let item = AVPlayerItem(url: url)
        self.queue = AVQueuePlayer(playerItem: item)
        queue.isMuted = true   // GIF 转出来的 MP4 没音轨
        self.looper = AVPlayerLooper(player: queue, templateItem: item)
        self.layer = AVPlayerLayer(player: queue)
        // videoGravity 由 PlayerLayerContainer 按 contentMode 设
    }
}

struct AnimatedVideoView: View {
    let url: URL
    var contentMode: ContentMode = .fill

    /// view 首次出现时 acquire 拿 layer,view 重建时 @State 保留,无需重新 acquire。
    @State private var layer: AVPlayerLayer?

    var body: some View {
        ZStack {
            if let layer {
                PlayerLayerContainer(layer: layer, contentMode: contentMode)
            } else {
                // acquire 完成前的占位(正常情况 <1ms,几乎看不到)
                Color.gray.opacity(0.08)
            }
        }
        .onAppear {
            // acquire 内部已 play();即便 view 之前消失时 release 过,这里也会重新 play
            layer = VideoPlayerPool.shared.acquire(url)
        }
        .onDisappear {
            // 只暂停 —— pool 还持有 layer,view 回来时 acquire 直接 play
            VideoPlayerPool.shared.release(url)
        }
    }
}

/// 把 pool 来的 layer 装到 view 的 backing layer 上。
/// `updateNSView` 每次都重设 layer 和 videoGravity,处理 SwiftUI 把 view
/// 复用到不同 cell 的情况(contentMode 可能变)。
private struct PlayerLayerContainer: NSViewRepresentable {
    let layer: AVPlayerLayer
    let contentMode: ContentMode

    func makeNSView(context: Context) -> NSView {
        let v = NSView(frame: .zero)
        v.wantsLayer = true
        v.layer = layer
        layer.videoGravity = contentMode == .fill ? .resizeAspectFill : .resizeAspect
        return v
    }

    func updateNSView(_ nsView: NSView, context: Context) {
        // view 复用时可能换了 layer 引用(不同 url);重新绑
        nsView.layer = layer
        layer.videoGravity = contentMode == .fill ? .resizeAspectFill : .resizeAspect
        // bounds 还没就绪时跳过(避免 0×0 闪烁)
        if nsView.bounds.size != .zero {
            layer.frame = nsView.bounds
        }
    }
}
