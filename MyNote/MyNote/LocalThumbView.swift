//
//  LocalThumbView.swift
//  MyNote
//
//  网格 cell 用的本地缩略图视图。读 Media.localThumbURL,带占位与缓存。
//

import SwiftUI

struct LocalThumbView: View {
    let media: Media
    @State private var image: NSImage?
    @State private var didTryLoad = false

    var body: some View {
        ZStack {
            if let image {
                Image(nsImage: image)
                    .resizable()
                    .scaledToFill()
            } else if didTryLoad {
                // 文件缺失或解码失败
                ZStack {
                    Color.gray.opacity(0.15)
                    Image(systemName: "photo")
                        .foregroundColor(.gray)
                        .font(.system(size: 20))
                }
            } else {
                ZStack {
                    Color.gray.opacity(0.08)
                    ProgressView().controlSize(.small)
                }
            }
        }
        .task(id: media.id) {
            guard let url = media.localThumbURL else {
                didTryLoad = true
                return
            }
            let loaded = await LocalImageLoader.shared.load(mediaId: media.id, url: url)
            await MainActor.run {
                self.image = loaded
                self.didTryLoad = true
            }
        }
    }
}
