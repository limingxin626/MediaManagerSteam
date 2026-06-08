//
//  MessageDetailPane.swift
//  MyNote
//
//  右侧消息详情面板 —— 当 viewModel.selectedMessage != nil 时显示。
//  Read-only:不显示「编辑」「删除」「拆分」等写操作按钮。
//

import SwiftUI

struct MessageDetailPane: View {
    let message: Message
    let isLoading: Bool
    let onClose: () -> Void
    /// 媒体点击 → 直接进预览(详情面板里点媒体就是预览,不再绕一层)。
    let onMediaPreview: (Int) -> Void

    var body: some View {
        VStack(spacing: 0) {
            header
            Divider()
            ScrollView {
                VStack(alignment: .leading, spacing: 16) {
                    actorRow
                    if let text = message.text, !text.isEmpty {
                        textBody(text)
                    }
                    if !message.tags.isEmpty {
                        tagChips
                    }
                    if !message.mediaItems.isEmpty {
                        MessageMediaGrid(
                            items: message.mediaItems,
                            clickBehavior: .directPreview,
                            onClick: onMediaPreview
                        )
                    }
                    if isLoading {
                        HStack {
                            Spacer()
                            ProgressView()
                                .controlSize(.small)
                            Spacer()
                        }
                        .padding(.vertical, 8)
                    }
                }
                .padding(16)
            }
        }
        .frame(maxWidth: .infinity, maxHeight: .infinity)
        .background(Color(nsColor: .windowBackgroundColor))
    }

    // MARK: - 顶部条:标题 + 时间 + ×

    private var header: some View {
        HStack(spacing: 8) {
            VStack(alignment: .leading, spacing: 2) {
                Text("消息详情")
                    .font(.system(size: 13, weight: .semibold))
                Text(absoluteDate(message.createdAt))
                    .font(.system(size: 11))
                    .foregroundColor(.secondary)
            }
            Spacer()
            // 星标(只读)
            Image(systemName: message.starred ? "star.fill" : "star")
                .font(.system(size: 12))
                .foregroundColor(message.starred ? .orange : .secondary)
                .help(message.starred ? "已收藏" : "未收藏")
            // 关闭
            Button(action: onClose) {
                Image(systemName: "xmark")
                    .font(.system(size: 11, weight: .medium))
                    .padding(4)
            }
            .buttonStyle(.plain)
            .foregroundColor(.secondary)
            .help("关闭详情(ESC)")
        }
        .padding(.horizontal, 16)
        .padding(.vertical, 10)
    }

    // MARK: - actor 行

    @ViewBuilder
    private var actorRow: some View {
        if let actorId = message.actorId, let name = message.actorName {
            HStack(spacing: 8) {
                ActorAvatarMiniView(actorId: actorId, size: 28)
                Text(name)
                    .font(.system(size: 13, weight: .medium))
                Spacer()
            }
        } else {
            HStack(spacing: 8) {
                Image(systemName: "person.crop.circle")
                    .resizable()
                    .frame(width: 28, height: 28)
                    .foregroundColor(.secondary)
                Text("无演员")
                    .font(.system(size: 13))
                    .foregroundColor(.secondary)
                Spacer()
            }
        }
    }

    // MARK: - 正文

    private func textBody(_ text: String) -> some View {
        let detected = detectLinks(text)
        return Text(detected)
            .font(.system(size: 14))
            .foregroundColor(.primary)
            .textSelection(.enabled)
            .fixedSize(horizontal: false, vertical: true)
    }

    private func detectLinks(_ text: String) -> AttributedString {
        var attr = AttributedString(text)
        let detector = try? NSDataDetector(types: NSTextCheckingResult.CheckingType.link.rawValue)
        let range = NSRange(location: 0, length: (text as NSString).length)
        if let matches = detector?.matches(in: text, options: [], range: range) {
            for m in matches {
                if let url = m.url, let swiftRange = Range(m.range, in: text) {
                    if let attrRange = Range(swiftRange, in: attr) {
                        attr[attrRange].link = url
                        attr[attrRange].foregroundColor = .accentColor
                    }
                }
            }
        }
        return attr
    }

    // MARK: - tag chips

    private var tagChips: some View {
        HStack(spacing: 6) {
            ForEach(message.tags) { tag in
                Text(tag.name)
                    .font(.system(size: 11))
                    .padding(.horizontal, 8)
                    .padding(.vertical, 3)
                    .background(Color.accentColor.opacity(0.12))
                    .foregroundColor(.accentColor)
                    .clipShape(Capsule())
            }
        }
    }

    // MARK: - helpers

    private func absoluteDate(_ iso: String) -> String {
        guard let date = MessageISO.formatter.date(from: iso) else { return iso }
        let f = DateFormatter()
        f.dateFormat = "yyyy年M月d日 HH:mm"
        return f.string(from: date)
    }
}
