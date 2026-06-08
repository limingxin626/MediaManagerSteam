//
//  MessageCard.swift
//  MyNote
//
//  消息卡(feed 内单条)—— 顶部 actor + 相对时间、正文、tag chips、媒体网格、底部条。
//
//  Read-only 行为:星标只展示不可点击;编辑 / 删除 / 合并 / 拆分等写操作按钮一律不显示。
//

import SwiftUI

struct MessageCard: View {
    let message: Message
    /// 是否处于选中态(与 viewModel.selectedMessage.id 匹配)
    let isSelected: Bool
    /// 媒体点击回调(feed 内点击不应直接进 preview,先开 detail)
    let onCardClick: () -> Void
    let onMediaClick: (Int) -> Void

    @State private var isHovered = false

    var body: some View {
        VStack(alignment: .leading, spacing: 8) {
            headerRow
            if let text = message.text, !text.isEmpty {
                textBody(text)
            }
            if !message.tags.isEmpty {
                tagChips
            }
            if !message.mediaItems.isEmpty {
                MessageMediaGrid(items: message.mediaItems, onClick: onMediaClick)
            }
            footerRow
        }
        .padding(12)
        .background(
            RoundedRectangle(cornerRadius: 10)
                .fill(isHovered || isSelected
                      ? Color.gray.opacity(0.10)
                      : Color.gray.opacity(0.04))
        )
        .overlay(
            RoundedRectangle(cornerRadius: 10)
                .stroke(isSelected ? Color.accentColor : Color.clear, lineWidth: 2)
        )
        .contentShape(Rectangle())
        .onHover { isHovered = $0 }
        .onTapGesture { onCardClick() }
    }

    // MARK: - 顶部行:actor + 时间

    private var headerRow: some View {
        HStack(spacing: 8) {
            actorAvatar
            VStack(alignment: .leading, spacing: 2) {
                Text(message.actorName ?? "无演员")
                    .font(.system(size: 13, weight: .semibold))
                    .foregroundColor(.primary)
                Text(RelativeTimeFormatter.format(message.createdAt))
                    .font(.system(size: 11))
                    .foregroundColor(.secondary)
            }
            Spacer()
        }
    }

    @ViewBuilder
    private var actorAvatar: some View {
        // 头像由 ActorAvatarMiniView 异步加载(单独组件避免在卡片 view body 内 await)
        if let actorId = message.actorId {
            ActorAvatarMiniView(actorId: actorId, size: 32)
        } else {
            Image(systemName: "person.crop.circle")
                .resizable()
                .frame(width: 32, height: 32)
                .foregroundColor(.secondary)
        }
    }

    // MARK: - 正文
    //
    // 全量 markdown 渲染(标题/列表/引用/代码块/表格/inline 标记/链接/图片)
    // —— 走 swift-markdown-ui,与 vue 端 `marked` 渲染基本对齐。
    // 视觉调校在 `MarkdownBody` 里统一,卡片和详情面板共用同一份样式。

    private func textBody(_ text: String) -> some View {
        MarkdownBody(text: text)
            .foregroundColor(.primary)
            .fixedSize(horizontal: false, vertical: true)
    }

    // MARK: - tag chips

    private var tagChips: some View {
        HStack(spacing: 6) {
            ForEach(message.tags.prefix(8)) { tag in
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

    // MARK: - 底部条:星标只读 + 媒体数 + id

    private var footerRow: some View {
        HStack(spacing: 8) {
            // 星标(只读,不接受点击)
            Image(systemName: message.starred ? "star.fill" : "star")
                .font(.system(size: 11))
                .foregroundColor(message.starred ? .orange : .secondary.opacity(0.5))
                .help(message.starred ? "已收藏(Mac 端暂不支持编辑)" : "未收藏(Mac 端暂不支持编辑)")

            if message.mediaCount > 0 {
                HStack(spacing: 3) {
                    Image(systemName: "photo")
                        .font(.system(size: 10))
                    Text("\(message.mediaCount)")
                        .font(.system(size: 11))
                }
                .foregroundColor(.secondary)
            }

            Spacer()

            // debug 用的 message id(小灰字)
            Text("#\(message.id)")
                .font(.system(size: 10, design: .monospaced))
                .foregroundColor(.secondary.opacity(0.5))
        }
    }
}

// MARK: - 演员头像(异步加载)

/// 头像异步加载,失败 / 无数据时显示 person.crop.circle 占位。
struct ActorAvatarMiniView: View {
    let actorId: Int
    let size: CGFloat

    @State private var image: NSImage?

    var body: some View {
        Group {
            if let image {
                Image(nsImage: image)
                    .resizable()
                    .scaledToFill()
            } else {
                Image(systemName: "person.crop.circle")
                    .resizable()
                    .foregroundColor(.secondary)
            }
        }
        .frame(width: size, height: size)
        .clipShape(Circle())
        .task(id: actorId) {
            await loadAvatar()
        }
    }

    @MainActor
    private func loadAvatar() async {
        // 拼出本地 URL(actorId → {DATA_ROOT}/data/actor_cover/{id}.webp)
        guard let root = Settings.dataRoot else { return }
        let url = root
            .appendingPathComponent("data", isDirectory: true)
            .appendingPathComponent("actor_cover", isDirectory: true)
            .appendingPathComponent("\(actorId).webp")
        let loaded = await LocalImageLoader.shared.loadActorAvatar(actorId: actorId, url: url)
        self.image = loaded
    }
}
