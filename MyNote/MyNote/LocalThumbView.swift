//
//  LocalThumbView.swift
//  MyNote
//
//  网格 cell 用的本地缩略图视图。读 Media.localThumbURL / localPreviewURL。
//
//  GIF 渲染路径(三级回退):
//    1. media.mimeType == image/gif + media.localPreviewURL 文件存在?
//       → AnimatedVideoView (AVPlayer 硬件解码,<5ms 冷启,首选)
//    2. thumb.webp 是 animated webp?
//       → AnimatedImageView (CGImageSource 软解,慢但能播)
//    3. 都不行?
//       → NSImage 显示 thumb.webp 第一帧
//
//  静态图(jpg/png)直接走 NSImage,无动画。
//

import SwiftUI

struct LocalThumbView: View {
    let media: Media
    @State private var image: NSImage?
    @State private var didTryLoad = false
    /// GIF 优先 MP4 preview 路径(URL 在 task 完成后置位,view body 切换到 AnimatedVideoView)
    @State private var previewURL: URL? = nil
    /// animated webp 兜底路径(MP4 缺失时)
    @State private var animatedThumbURL: URL? = nil

    var body: some View {
        GeometryReader { geo in
            ZStack {
                if let url = previewURL {
                    // GIF 走硬件解码 —— pool 复用 AVPlayer,<1ms 命中,无 vmc2BuildDecompression 开销
                    AnimatedVideoView(url: url, contentMode: .fill)
                        .frame(width: geo.size.width, height: geo.size.height)
                        .clipped()
                } else if let url = animatedThumbURL {
                    // MP4 缺失时回退到 animated webp(CGImageSource 软解,慢但能播)
                    AnimatedImageView(url: url, contentMode: .fill)
                        .frame(width: geo.size.width, height: geo.size.height)
                        .clipped()
                } else if let image {
                    Image(nsImage: image)
                        .resizable()
                        .scaledToFill()
                        .frame(width: geo.size.width, height: geo.size.height)
                        .clipped()
                } else {
                    placeholder
                }
            }
            .frame(width: geo.size.width, height: geo.size.height)
        }
        .task(id: media.id) {
            // 预热静态 thumb 缓存(给其他场景用),并显示兜底图
            if let url = media.localThumbURL {
                let loaded = await LocalImageLoader.shared.load(mediaId: media.id, url: url)
                await MainActor.run {
                    self.image = loaded
                    self.didTryLoad = true
                }
            } else {
                await MainActor.run { self.didTryLoad = true }
            }
            // GIF 优先 MP4 preview(若存在)—— 这是主要动画路径
            if media.mimeType == "image/gif",
               let p = media.localPreviewURL,
               FileManager.default.fileExists(atPath: p.path) {
                await MainActor.run { self.previewURL = p }
                return
            }
            // 兜底:animated webp
            if let thumbURL = media.localThumbURL,
               case .animated = AnimatedImageFormatDetector.detect(url: thumbURL) {
                await MainActor.run { self.animatedThumbURL = thumbURL }
            }
        }
    }

    @ViewBuilder
    private var placeholder: some View {
        ZStack {
            Color.gray.opacity(0.08)
            Image(systemName: "photo")
                .foregroundColor(.gray)
                .font(.system(size: 20))
        }
    }
}
