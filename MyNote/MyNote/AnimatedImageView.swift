//
//  AnimatedImageView.swift
//  MyNote
//
//  用 CGImageSource 读 GIF / animated webp 的所有帧,Timer 切帧。
//  NSImage(contentsOf:) 在 macOS 上对这两种格式都只解首帧,
//  真正要播动画得自己驱动 frame timeline。
//
//  支持:
//    - image/gif
//    - image/webp (animated,多帧)
//
//  用法:
//    AnimatedImageView(url: media.localFileURL!, contentMode: .fit)
//        .frame(width: 600, height: 400)
//

import SwiftUI
import AppKit
import Combine
import ImageIO
import UniformTypeIdentifiers

/// `NSImage` / `CGImageSource` 对"单帧 vs 多帧"格式的探测结果。
enum AnimatedImageFormat {
    case staticImage
    case animated(frameCount: Int, loopCount: Int)
    case unsupported
}

enum AnimatedImageFormatDetector {
    /// 探测文件是否是动画格式,以及帧数 / 循环次数。
    /// 优先看扩展名 + UTI 决定用哪类 source;gifs 用 kCGImagePropertyGIFDictionary,
    /// webp 用 kCGImagePropertyWebPDictionary 读 frame count。
    static func detect(url: URL) -> AnimatedImageFormat {
        guard let src = CGImageSourceCreateWithURL(url as CFURL, nil) else {
            return .unsupported
        }
        let count = CGImageSourceGetCount(src)
        guard count > 0 else { return .unsupported }
        if count == 1 { return .staticImage }

        // 多帧 → 读 properties 看 loop count(0 = 无限)
        guard let props = CGImageSourceCopyProperties(src, nil) as? [CFString: Any] else {
            return .animated(frameCount: count, loopCount: 0)
        }
        let loopCount: Int
        if let gif = props[kCGImagePropertyGIFDictionary] as? [CFString: Any],
           let loop = gif[kCGImagePropertyGIFLoopCount] as? Int {
            loopCount = loop
        } else if let webp = props[kCGImagePropertyWebPDictionary] as? [CFString: Any],
                  let loop = webp[kCGImagePropertyWebPLoopCount] as? Int {
            loopCount = loop
        } else {
            loopCount = 0
        }
        return .animated(frameCount: count, loopCount: loopCount)
    }
}

/// 帧数据(预先解码的 CGImage + 持续时间毫秒)。
struct AnimatedFrame {
    let image: CGImage
    let durationMs: Int
}

// MARK: - 帧缓存(actor 隔离,跨 cell 共享)

/// 同一 URL 的帧只解码一次,后续 cell 直接拿 cache。
/// 并发的 cell 触发同一 URL 时,共享同一个 Task(不会重复解)。
/// 内存压力:不设上限(动画帧一般 1-3 MB × 几十个 URL),
/// 如果将来要限,加 NSCache + countLimit / totalCostLimit 即可。
actor AnimatedImageFrameCache {
    static let shared = AnimatedImageFrameCache()

    private var cache: [URL: [AnimatedFrame]] = [:]
    private var inflight: [URL: Task<[AnimatedFrame], Never>] = [:]

    /// 取帧:命中直接返回;未命中(且未在加载)启动后台解码,等结果。
    /// 同一 URL 的并发请求会复用 inflight 任务。
    func frames(for url: URL) async -> [AnimatedFrame] {
        if let cached = cache[url] { return cached }
        if let task = inflight[url] { return await task.value }
        let task = Task<[AnimatedFrame], Never> { [weak self] in
            await self?.decode(url: url) ?? []
        }
        inflight[url] = task
        let result = await task.value
        cache[url] = result
        inflight[url] = nil
        return result
    }

    /// 后台解码:CGImageSourceCreateWithURL + 逐帧 CGImageSourceCreateImageAtIndex。
    private func decode(url: URL) async -> [AnimatedFrame] {
        guard let src = CGImageSourceCreateWithURL(url as CFURL, nil) else { return [] }
        let count = CGImageSourceGetCount(src)
        guard count > 0 else { return [] }
        return await Task.detached(priority: .userInitiated) { () -> [AnimatedFrame] in
            var result: [AnimatedFrame] = []
            result.reserveCapacity(count)
            for i in 0..<count {
                let opts: [CFString: Any] = [
                    kCGImageSourceShouldCacheImmediately: true,
                ]
                guard let cg = CGImageSourceCreateImageAtIndex(src, i, opts as CFDictionary) else {
                    continue
                }
                var duration = 100
                if let frameProps = CGImageSourceCopyPropertiesAtIndex(src, i, nil) as? [CFString: Any] {
                    if let gif = frameProps[kCGImagePropertyGIFDictionary] as? [CFString: Any],
                       let d = gif[kCGImagePropertyGIFDelayTime] as? Double {
                        duration = Int(d * 1000)
                    } else if let webp = frameProps[kCGImagePropertyWebPDictionary] as? [CFString: Any],
                              let d = webp[kCGImagePropertyWebPDelayTime] as? Double {
                        duration = Int(d * 1000)
                    }
                }
                if duration < 20 { duration = 100 }
                result.append(AnimatedFrame(image: cg, durationMs: duration))
            }
            return result
        }.value
    }
}

/// 预加载所有帧到内存。`isPaused` 时停在当前帧;`start()` 后用 Timer 切帧。
/// 解码只做一次,task 取消或 view 消失时停止 timer。
@MainActor
final class AnimatedImagePlayer: ObservableObject {
    @Published private(set) var currentIndex: Int = 0
    @Published private(set) var isPaused: Bool = false
    /// 解码进度 0..1(预加载阶段)。详情大图显示 progress;网格 cell 跳过这步。
    @Published private(set) var loadProgress: Double = 0
    /// 帧就绪(frames 非空)。cell 用这个判断要不要显示 loading overlay。
    @Published private(set) var isReady: Bool = false

    private(set) var frames: [AnimatedFrame] = []
    private var loopCount: Int = 0          // 0 = 无限
    private var loopsDone: Int = 0
    private var timer: Timer?

    func load(url: URL) async {
        // 走共享 cache —— 同一 URL 多次 load 只解码一次
        let decoded = await AnimatedImageFrameCache.shared.frames(for: url)
        guard !decoded.isEmpty else { return }

        // 同样读 loop count
        if let src = CGImageSourceCreateWithURL(url as CFURL, nil),
           let props = CGImageSourceCopyProperties(src, nil) as? [CFString: Any] {
            if let gif = props[kCGImagePropertyGIFDictionary] as? [CFString: Any],
               let l = gif[kCGImagePropertyGIFLoopCount] as? Int {
                loopCount = l
            } else if let webp = props[kCGImagePropertyWebPDictionary] as? [CFString: Any],
                      let l = webp[kCGImagePropertyWebPLoopCount] as? Int {
                loopCount = l
            }
        }

        frames = decoded
        loadProgress = 1
        currentIndex = 0
        isReady = true
    }

    func start() {
        // 不再检查 isPaused——这是 bug 根因:pause 后 start() 永远 early-return。
        // 想要从 pause 恢复,直接 start(),会自动覆盖旧 timer。
        guard !frames.isEmpty else { return }
        isPaused = false
        scheduleNext()
    }

    func pause() {
        isPaused = true
        timer?.invalidate()
        timer = nil
    }

    func reset() {
        pause()
        currentIndex = 0
    }

    deinit {
        timer?.invalidate()
    }

    private func scheduleNext() {
        timer?.invalidate()
        guard !isPaused, !frames.isEmpty else { return }
        let frame = frames[currentIndex]
        timer = Timer.scheduledTimer(withTimeInterval: Double(frame.durationMs) / 1000.0, repeats: false) { [weak self] _ in
            Task { @MainActor in self?.advance() }
        }
    }

    private func advance() {
        guard !frames.isEmpty else { return }
        let next = currentIndex + 1
        if next >= frames.count {
            // 跑完一轮
            loopsDone += 1
            if loopCount > 0 && loopsDone >= loopCount {
                // 到达循环上限,停在最后一帧
                return
            }
            currentIndex = 0
        } else {
            currentIndex = next
        }
        scheduleNext()
    }
}

/// SwiftUI 视图:把 AnimatedImagePlayer 包出来,接 url + 缩放模式。
/// view 出现时 start,消失时 pause,断网 / 切 url 时 reset 重新 load。
struct AnimatedImageView: View {
    let url: URL
    var contentMode: ContentMode = .fit

    @StateObject private var player = AnimatedImagePlayer()
    @Environment(\.scenePhase) private var scenePhase

    var body: some View {
        ZStack {
            // 1) 解码完成 → 显动画帧
            if player.isReady,
               player.frames.indices.contains(player.currentIndex) {
                Image(decorative: player.frames[player.currentIndex].image,
                      scale: 1, orientation: .up)
                    .resizable()
                    .aspectRatio(contentMode: contentMode)
            }
            // 2) 解码中 → 显眼 loading 覆盖(深色蒙层 + spinner + "解码中…"文字)
            else if !player.isReady {
                ZStack {
                    Color.black.opacity(0.15)
                    VStack(spacing: 8) {
                        ProgressView()
                            .controlSize(.regular)
                        Text("解码中…")
                            .font(.caption2)
                            .foregroundColor(.secondary)
                    }
                    .padding(12)
                    .background(.regularMaterial, in: RoundedRectangle(cornerRadius: 8))
                }
                .transition(.opacity)
            }
            // 3) 解码完成但 frames 为空(失败) → photo 占位
            else {
                Image(systemName: "photo")
                    .foregroundColor(.gray)
            }
        }
        .animation(.easeInOut(duration: 0.15), value: player.isReady)
        .task(id: url) {
            await player.load(url: url)
            player.start()
        }
        .onAppear { player.start() }    // cell 滚回视口时恢复
        .onDisappear { player.pause() } // 滚出视口暂停,省 CPU
        .onChange(of: scenePhase) { _, phase in
            switch phase {
            case .active: player.start()
            default:      player.pause()
            }
        }
    }
}
