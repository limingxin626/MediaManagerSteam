//
//  MessageCard.swift
//  MyNote
//
//  消息卡(feed 内单条)—— 顶部 actor + 相对时间、正文、tag chips、媒体网格、底部条。
//
//  两态:
//    - 只读态(默认):正文 markdown 渲染、tag 只展示、媒体网格可点开预览。
//      右下角有一个轻量「编辑」按钮(hover 才显著),点击后进编辑态。
//    - 编辑态:正文换成 TextEditor;tag chips 右侧出现「x」按钮可移除,
//      末尾加「+」按钮弹 popover 多选 availableTags;底部出现「取消 / 保存」。
//      媒体网格、actor 头像、issue 等仍是只读(本期不动)。
//  星标:两态下都是可点击 Button —— 走 viewModel.toggleStar(乐观更新)。
//
//  写入路径:viewModel.commitEdit / toggleStar → APIClient PATCH → backend
//  message_service(复用 #hashtag 解析、SyncLog 等)。Mac GRDB 是 read-only,
//  不在本端直接写库。
//
//  点击行为:卡内媒体网格在两态下均可点 —— 透传 onMediaClick 给上层,
//  由 MessagesView 打开 MediaDetailView。
//

import SwiftUI

struct MessageCard: View {
    let message: Message

    /// 用于触发 mutation —— Save / Cancel / star toggle / tag popover 都需要它。
    @ObservedObject var viewModel: MessagesViewModel

    /// 媒体网格里点击某张图 / +N 徽章时回调,参数是 mediaItems 的 index
    ///(在 maxPreviewItems=10 的前缀内,与 visibleItems 的 index 一致)。
    /// MessagesView 在此回调里调 openPreview(message:startIndex:)。
    var onMediaClick: (Int) -> Void = { _ in }

    @State private var isHovered = false

    // MARK: - 编辑态

    /// 是否处于编辑态。默认 false = 只读;点「编辑」→ true,进入草稿模式。
    @State private var isEditing = false

    /// 正文草稿。进入编辑态时从 message.text 拷贝;Cancel 丢弃,Save 提交。
    @State private var draftText: String = ""

    /// tag 草稿(只存 id 集合)。chip 删除从这里移除,popover 多选写这里。
    /// Save 时传给 backend 替换原 tag 集。
    @State private var draftTagIds: Set<Int> = []

    /// 保存中标志 —— Save 按钮按下后置 true,避免重复点击;成功 / 失败都置回 false。
    @State private var isSaving = false

    /// tag popover 显隐
    @State private var showTagPopover = false

    var body: some View {
        VStack(alignment: .leading, spacing: 8) {
            headerRow
            textSection
            tagSection
            if !message.mediaItems.isEmpty {
                MessageMediaGrid5(mediaItems: message.mediaItems, onClick: onMediaClick)
            }
            footerRow
        }
        .padding(12)
        .background(
            RoundedRectangle(cornerRadius: 10)
                .fill(backgroundFill)
        )
        .overlay(
            // 编辑态加一层细边框强化模式感,避免和相邻卡片视觉粘连
            RoundedRectangle(cornerRadius: 10)
                .stroke(isEditing ? Color.accentColor.opacity(0.5) : Color.clear, lineWidth: 1)
        )
        .onHover { isHovered = $0 }
    }

    private var backgroundFill: Color {
        if isEditing {
            return Color.accentColor.opacity(0.06)
        }
        return isHovered ? Color.gray.opacity(0.10) : Color.gray.opacity(0.04)
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
        if let actorId = message.actorId {
            ActorAvatarMiniView(actorId: actorId, size: 32)
        } else {
            Image(systemName: "person.crop.circle")
                .resizable()
                .frame(width: 32, height: 32)
                .foregroundColor(.secondary)
        }
    }

    // MARK: - 正文(两态)

    @ViewBuilder
    private var textSection: some View {
        if isEditing {
            TextEditor(text: $draftText)
                .font(.system(size: 13))
                .frame(minHeight: 80, maxHeight: 240)
                .padding(6)
                .background(
                    RoundedRectangle(cornerRadius: 6)
                        .fill(Color(nsColor: .textBackgroundColor))
                )
                .overlay(
                    RoundedRectangle(cornerRadius: 6)
                        .stroke(Color.secondary.opacity(0.3), lineWidth: 1)
                )
        } else if let text = message.text, !text.isEmpty {
            // 全量 markdown 渲染,与 vue 端 `marked` 对齐;详见 MarkdownBody。
            MarkdownBody(text: text)
                .foregroundColor(.primary)
                .fixedSize(horizontal: false, vertical: true)
        }
    }

    // MARK: - tag 区(两态)

    @ViewBuilder
    private var tagSection: some View {
        if isEditing {
            editingTagRow
        } else if !message.tags.isEmpty {
            readonlyTagChips
        }
    }

    private var readonlyTagChips: some View {
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

    /// 编辑态的 tag 行:草稿 chips 各自带 x 移除按钮,末尾加 + 弹 popover 多选。
    private var editingTagRow: some View {
        // 用 FlowLayout 类的写法成本高,先用普通 HStack;tag 多时容器允许换行可走
        // ViewThatFits/WrappingHStack。当前先求最小可用,8 个以内显示宽度足够。
        HStack(spacing: 6) {
            ForEach(draftTagIdsSorted, id: \.self) { tagId in
                editableTagChip(tagId: tagId)
            }
            Button {
                showTagPopover.toggle()
            } label: {
                Image(systemName: "plus.circle")
                    .font(.system(size: 13))
                    .foregroundColor(.accentColor)
            }
            .buttonStyle(.plain)
            .popover(isPresented: $showTagPopover, arrowEdge: .bottom) {
                TagPickerPopover(
                    availableTags: viewModel.availableTags,
                    selected: $draftTagIds
                )
            }
        }
    }

    /// 草稿 tag id 列表,按 availableTags 顺序排,避免每次选 / 删都跳序。
    private var draftTagIdsSorted: [Int] {
        // availableTags 已按 message_count desc 排,直接 filter 取交集即可。
        viewModel.availableTags.map(\.id).filter { draftTagIds.contains($0) }
    }

    private func editableTagChip(tagId: Int) -> some View {
        let name = viewModel.availableTags.first(where: { $0.id == tagId })?.name
            ?? message.tags.first(where: { $0.id == tagId })?.name
            ?? "#\(tagId)"
        return HStack(spacing: 4) {
            Text(name)
                .font(.system(size: 11))
            Button {
                draftTagIds.remove(tagId)
            } label: {
                Image(systemName: "xmark")
                    .font(.system(size: 9, weight: .bold))
            }
            .buttonStyle(.plain)
            .foregroundColor(.accentColor.opacity(0.7))
        }
        .padding(.leading, 8)
        .padding(.trailing, 6)
        .padding(.vertical, 3)
        .background(Color.accentColor.opacity(0.12))
        .foregroundColor(.accentColor)
        .clipShape(Capsule())
    }

    // MARK: - 底部条:星标 + 媒体数 + id + 编辑控件

    private var footerRow: some View {
        HStack(spacing: 8) {
            // 星标:两态下都可点击 → 乐观翻转 + backend PATCH
            Button {
                Task { await viewModel.toggleStar(messageId: message.id) }
            } label: {
                Image(systemName: message.starred ? "star.fill" : "star")
                    .font(.system(size: 12))
                    .foregroundColor(message.starred ? .orange : .secondary.opacity(0.6))
            }
            .buttonStyle(.plain)
            .help(message.starred ? "取消收藏" : "收藏")

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

            // 编辑控件:只读态显示「编辑」(hover 才显眼);编辑态显示「取消 / 保存」。
            if isEditing {
                Button("取消") {
                    cancelEdit()
                }
                .buttonStyle(.plain)
                .font(.system(size: 11))
                .foregroundColor(.secondary)
                .disabled(isSaving)

                Button {
                    Task { await saveEdit() }
                } label: {
                    if isSaving {
                        ProgressView().controlSize(.mini)
                    } else {
                        Text("保存").font(.system(size: 11, weight: .semibold))
                    }
                }
                .buttonStyle(.borderedProminent)
                .controlSize(.small)
                .disabled(isSaving)
            } else {
                Button {
                    beginEdit()
                } label: {
                    Image(systemName: "pencil")
                        .font(.system(size: 11))
                }
                .buttonStyle(.plain)
                .foregroundColor(.secondary.opacity(isHovered ? 0.9 : 0.4))
                .help("编辑")
            }

            // debug 用的 message id(小灰字)
            Text("#\(message.id)")
                .font(.system(size: 10, design: .monospaced))
                .foregroundColor(.secondary.opacity(0.5))
        }
    }

    // MARK: - 编辑生命周期

    private func beginEdit() {
        draftText = message.text ?? ""
        draftTagIds = Set(message.tags.map(\.id))
        isEditing = true
    }

    private func cancelEdit() {
        isEditing = false
        draftText = ""
        draftTagIds = []
        showTagPopover = false
    }

    private func saveEdit() async {
        isSaving = true
        defer { isSaving = false }
        let originalTagIds = Set(message.tags.map(\.id))
        let textChanged = (draftText != (message.text ?? ""))
        let tagsChanged = (draftTagIds != originalTagIds)
        // 没有任何变化直接退出编辑态,不发请求
        guard textChanged || tagsChanged else {
            cancelEdit()
            return
        }
        let ok = await viewModel.commitEdit(
            messageId: message.id,
            text: textChanged ? draftText : nil,
            // 传 tagIds 后端按显式 tag 替换、不再解析正文 #hashtag。
            // 这里:tag 改了就显式传(替换);没改就 nil 让后端按 text 重抽
            //(text 改了 → #hashtag 重抽;text 没改 → 后端 tag_ids=None 不动)。
            tagIds: tagsChanged ? Array(draftTagIds) : nil
        )
        if ok {
            cancelEdit()
        }
    }
}

// MARK: - Tag 多选 popover

/// 编辑态 tag 多选器。展示 availableTags 的 toggle 列表,顶部带搜索框。
/// 选 / 取消选实时写回 selected 集合,无 OK / Cancel —— 点 popover 外即关闭。
private struct TagPickerPopover: View {
    let availableTags: [Tag]
    @Binding var selected: Set<Int>

    @State private var search: String = ""

    private var filtered: [Tag] {
        guard !search.isEmpty else { return availableTags }
        return availableTags.filter { $0.name.localizedCaseInsensitiveContains(search) }
    }

    var body: some View {
        VStack(alignment: .leading, spacing: 6) {
            TextField("搜索 tag…", text: $search)
                .textFieldStyle(.roundedBorder)
                .font(.system(size: 12))

            ScrollView {
                VStack(alignment: .leading, spacing: 2) {
                    ForEach(filtered) { tag in
                        tagRow(tag)
                    }
                    if filtered.isEmpty {
                        Text("没有匹配的 tag")
                            .font(.system(size: 11))
                            .foregroundColor(.secondary)
                            .padding(.vertical, 8)
                    }
                }
            }
            .frame(maxHeight: 280)
        }
        .padding(10)
        .frame(width: 240)
    }

    private func tagRow(_ tag: Tag) -> some View {
        let isOn = selected.contains(tag.id)
        return Button {
            if isOn {
                selected.remove(tag.id)
            } else {
                selected.insert(tag.id)
            }
        } label: {
            HStack(spacing: 6) {
                Image(systemName: isOn ? "checkmark.square.fill" : "square")
                    .font(.system(size: 12))
                    .foregroundColor(isOn ? .accentColor : .secondary)
                Text(tag.name)
                    .font(.system(size: 12))
                Spacer()
                Text("\(tag.messageCount)")
                    .font(.system(size: 10))
                    .foregroundColor(.secondary.opacity(0.6))
            }
            .padding(.horizontal, 6)
            .padding(.vertical, 3)
            .contentShape(Rectangle())
        }
        .buttonStyle(.plain)
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
