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
//  / AVPlayerLooper(不共享 layer!)。VideoToolbox session 创建绑在
//  AVPlayer 上,30-50ms/cell,几十 cell 排队会卡;cache 命中时 <1ms。
//
//  layer 策略:每个 view 自己 create AVPlayerLayer,通过 `makeBackingLayer`
//  直接当 view 的 backing layer —— frame 自动跟 view bounds 走(view 销毁
//  layer 自动释放),不污染其它 view。
//
//  翻页 / 父级换 url:SwiftUI 会**复用**本 view(同位置同类型),@State 保留;
//  用 onChange(of: url, initial: true) 重新 acquire 新 player,并通过
//  updateNSView 把新 player 喂给 backing AVPlayerLayer。
//

import SwiftUI
import AVFoundation
import AVKit

/// 按 URL 共享的 AVPlayer 池。跨 cell 复用避免反复 create / destroy
/// VideoToolbox session(view 出现/消失不释放,只 play/pause)。
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

    /// pool 拿到的 player。view 首次出现时 acquire 拿,view 重建时 @State 保留。
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
        // 关键:监听 url 变化 —— 父级用新 url 复用本 view(详情翻页)时,@State
        // player 是老的,不重新 acquire 就会卡死。onChange 把老 player 释放、
        // 新 player 拿进来,@State 更新触发 body 重算,PlayerLayerContainer
        // 收到新 player。initial: true 让首次出现也走同一路径,逻辑统一。
        .onChange(of: url, initial: true) { oldUrl, newUrl in
            if oldUrl != newUrl {
                VideoPlayerPool.shared.release(oldUrl)
            }
            player = VideoPlayerPool.shared.acquire(newUrl)
        }
        // view 真正从 view tree 移除时,释放 pool(等下次 onChange/出现再 acquire)
        .onDisappear {
            VideoPlayerPool.shared.release(url)
        }
    }
}

/// AVPlayerLayer 作为 backing layer 的 NSView 子类。
/// 关键:`makeBackingLayer` 决定 backing layer 类型,frame 自动跟 view bounds。
///
/// `player` 是 `var` 而非 `let`:父级 re-render 换 player 时,`updateNSView`
/// 调 `host.update(player:contentMode:)`,把 backing `AVPlayerLayer.player`
/// 换成新的 —— 否则 view 复用后一直播老 player。
private final class PlayerLayerHostView: NSView {
    var player: AVPlayer
    var contentMode: ContentMode

    init(player: AVPlayer, contentMode: ContentMode) {
        self.player = player
        self.contentMode = contentMode
        super.init(frame: .zero)
        wantsLayer = true
        // wantsLayer = true 触发 makeBackingLayer(),无需再设 layer
    }

    required init?(coder: NSCoder) { fatalError() }

    override func makeBackingLayer() -> CALayer {
        let layer = AVPlayerLayer(player: player)
        layer.videoGravity = contentMode == .fill ? .resizeAspectFill : .resizeAspect
        layer.backgroundColor = NSColor.clear.cgColor
        return layer
    }

    /// 父级 re-render 换 player / contentMode 时调。只在 player 真的变了时
    /// 才赋给 AVPlayerLayer(player 引用没变时跳过,避免无谓重置导致画面闪)。
    /// videoGravity 每次都设(便宜,允许 contentMode 变化实时生效)。
    func update(player: AVPlayer, contentMode: ContentMode) {
        let playerChanged = self.player !== player
        self.player = player
        self.contentMode = contentMode
        guard let playerLayer = layer as? AVPlayerLayer else { return }
        if playerChanged {
            playerLayer.player = player
        }
        playerLayer.videoGravity = contentMode == .fill ? .resizeAspectFill : .resizeAspect
    }
}

private struct PlayerLayerContainer: NSViewRepresentable {
    let player: AVPlayer
    let contentMode: ContentMode

    func makeNSView(context: Context) -> NSView {
        PlayerLayerHostView(player: player, contentMode: contentMode)
    }

    func updateNSView(_ nsView: NSView, context: Context) {
        // SwiftUI 复用 NSView 时调(父级 re-render 换 player),把新 player
        // 喂给 backing AVPlayerLayer,否则老 player 一直播 → 翻页卡死
        guard let host = nsView as? PlayerLayerHostView else { return }
        host.update(player: player, contentMode: contentMode)
    }
}
