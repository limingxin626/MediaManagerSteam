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
//  性能关键 —— `VideoPlayerPool` 按 URL 跨 cell 共享 AVPlayer / AVPlayerItem
//  / AVPlayerLooper(不共享 layer!),避免反复 create / destroy VideoToolbox
//  session —— vmc2BuildDecompressionSession 单次要 30-50ms,几十 cell 排队
//  = 明显卡顿。
//
//  layer 每个 view 自己创建并 addSublayer 到 view 的 backing layer 上 ——
//  view 销毁 layer 自动清理,detail ↔ grid 切来切去不会污染状态(老方案把
//  layer 也共享,导致 detail 关闭后 grid cell layer 状态混乱 → 空白)。
//

import SwiftUI
import AVFoundation
import AVKit

/// 按 URL 共享的 AVPlayer 池。跨 cell 复用避免反复 create / destroy
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

    /// 拿 player 并立刻 play。cache 命中时不重建 AVPlayer(VideoToolbox session
    /// 复用),只 play。
    func acquire(_ url: URL) -> AVPlayer {
        if let bundle = cache.object(forKey: url as NSURL) {
            bundle.queue.play()
            return bundle.queue
        }
        let bundle = PlayerBundle(url: url)
        cache.setObject(bundle, forKey: url as NSURL)
        bundle.queue.play()
        return bundle.queue
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

/// 不可变 bundle:queue / looper 一起创建,一起释放,绑死同一个 url。
/// 不持有 layer —— 每个 view 自己创建独立的 AVPlayerLayer(便宜,且不
/// 跨 view 共享状态)。
private final class PlayerBundle {
    let queue: AVQueuePlayer
    let looper: AVPlayerLooper

    init(url: URL) {
        let item = AVPlayerItem(url: url)
        self.queue = AVQueuePlayer(playerItem: item)
        queue.isMuted = true   // GIF 转出来的 MP4 没音轨
        self.looper = AVPlayerLooper(player: queue, templateItem: item)
    }
}

struct AnimatedVideoView: View {
    let url: URL
    var contentMode: ContentMode = .fill

    /// pool 拿到的 player。view 首次出现时 acquire 拿,view 重建时 @State 保留,
    /// 无需重新 acquire。
    @State private var player: AVPlayer?

    var body: some View {
        ZStack {
            if let player {
                PlayerLayerContainer(player: player, contentMode: contentMode)
            } else {
                // acquire 完成前的占位(正常情况 <1ms,几乎看不到)
                Color.gray.opacity(0.08)
            }
        }
        .onAppear {
            // acquire 内部已 play();即便 view 之前消失时 release 过,这里也会重新 play
            player = VideoPlayerPool.shared.acquire(url)
        }
        .onDisappear {
            // 只暂停 player —— pool 还持有 player,view 回来时 acquire 直接 play。
            // 注意:不暂停 layer 也没有(每个 view 自己 layer,随 view 销毁自动清理)
            VideoPlayerPool.shared.release(url)
        }
    }
}

/// 把 pool 来的 player 装到一个**新建**的 AVPlayerLayer 上,addSublayer 到
/// view 的 backing layer。每个 view 拥有自己的 layer,layer 生命周期 = view
/// 生命周期,关闭 detail 不会污染 grid 状态。
private struct PlayerLayerContainer: NSViewRepresentable {
    let player: AVPlayer
    let contentMode: ContentMode

    func makeCoordinator() -> Coordinator { Coordinator() }

    func makeNSView(context: Context) -> NSView {
        let v = NSView(frame: .zero)
        v.wantsLayer = true
        // 关键:每个 view 自己创建 layer —— 而不是 v.layer = sharedLayer。
        // 后者会跨 view 共享 backing layer,detail 关闭后 grid 拿到半死状态的
        // layer 渲染失败 → 空白。
        let layer = AVPlayerLayer(player: player)
        layer.videoGravity = contentMode == .fill ? .resizeAspectFill : .resizeAspect
        context.coordinator.playerLayer = layer
        v.layer?.addSublayer(layer)
        return v
    }

    func updateNSView(_ nsView: NSView, context: Context) {
        // bounds 还没就绪时跳过(避免 0×0 闪烁)
        guard let layer = context.coordinator.playerLayer,
              nsView.bounds.size != .zero else { return }
        layer.videoGravity = contentMode == .fill ? .resizeAspectFill : .resizeAspect
        layer.frame = nsView.bounds
    }

    final class Coordinator {
        var playerLayer: AVPlayerLayer?
    }
}
