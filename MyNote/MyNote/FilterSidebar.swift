//
//  FilterSidebar.swift
//  MyNote
//
//  消息流的左侧过滤侧栏 —— 标签 / 演员 / Issue 三组条目,macOS 风格 List(selection:)。
//  三个分组互斥:点 tag 清 actor + issue,反之亦然(同 MessagesViewModel.selectFilter)。
//
//  窄屏(< 800pt)时改用 toolbar dropdown —— 通过 `isCompact` 参数控制。
//

import SwiftUI

struct FilterSidebar: View {
    @ObservedObject var viewModel: MessagesViewModel

    /// 当前选中的过滤器(单一来源)—— 用 enum 包装避免多个 optional 同时非空
    enum Selection: Hashable {
        case tag(Int)
        case actor(Int)
        case issue(Int)
    }

    var selection: Binding<Selection?> {
        Binding(
            get: {
                if let id = viewModel.selectedTagId { return .tag(id) }
                if let id = viewModel.selectedActorId { return .actor(id) }
                if let id = viewModel.selectedIssueId { return .issue(id) }
                return nil
            },
            set: { newValue in
                Task { @MainActor in
                    switch newValue {
                    case .tag(let id):
                        await viewModel.selectFilter(kind: .tag, id: id)
                    case .actor(let id):
                        await viewModel.selectFilter(kind: .actor, id: id)
                    case .issue(let id):
                        await viewModel.selectFilter(kind: .issue, id: id)
                    case .none:
                        // 清空当前过滤器
                        if viewModel.selectedTagId != nil {
                            await viewModel.selectFilter(kind: .tag, id: nil)
                        } else if viewModel.selectedActorId != nil {
                            await viewModel.selectFilter(kind: .actor, id: nil)
                        } else if viewModel.selectedIssueId != nil {
                            await viewModel.selectFilter(kind: .issue, id: nil)
                        }
                    }
                }
            }
        )
    }

    var body: some View {
        List(selection: selection) {
            tagSection
            actorSection
            issueSection
        }
        .listStyle(.sidebar)
        .frame(minWidth: 200, idealWidth: 220, maxWidth: 280)
    }

    // MARK: - 标签

    private var tagSection: some View {
        Section("标签") {
            ForEach(viewModel.availableTags) { tag in
                HStack {
                    Text(tag.name)
                    Spacer()
                    Text("\(tag.messageCount)")
                        .font(.system(size: 10))
                        .foregroundColor(.secondary)
                }
                .tag(Selection.tag(tag.id))
            }
        }
    }

    // MARK: - 演员(「无演员」是首项,占位 actorId == 0)

    private var actorSection: some View {
        Section("演员") {
            HStack {
                Text("无演员")
                    .foregroundColor(.secondary)
                Spacer()
            }
            .tag(Selection.actor(0))
            ForEach(viewModel.availableActors) { actor in
                HStack {
                    Text(actor.name)
                    Spacer()
                    Text("\(actor.messageCount)")
                        .font(.system(size: 10))
                        .foregroundColor(.secondary)
                }
                .tag(Selection.actor(actor.id))
            }
        }
    }

    // MARK: - Issue(「无 issue」是首项,占位 issueId == 0)

    private var issueSection: some View {
        Section("Issue") {
            HStack {
                Text("无 issue")
                    .foregroundColor(.secondary)
                Spacer()
            }
            .tag(Selection.issue(0))
            ForEach(viewModel.availableIssues) { issue in
                HStack {
                    Text(issue.title)
                        .lineLimit(1)
                }
                .tag(Selection.issue(issue.id))
            }
        }
    }
}

// MARK: - 窄屏 dropdown 变体

/// 窄屏(< 800pt)用的紧凑版:把三个过滤压成一个 toolbar dropdown menu。
struct FilterMenuCompact: View {
    @ObservedObject var viewModel: MessagesViewModel

    var body: some View {
        Menu {
            Section("标签") {
                ForEach(viewModel.availableTags) { tag in
                    Button {
                        Task { await viewModel.selectFilter(kind: .tag, id: tag.id) }
                    } label: {
                        Label("\(tag.name) (\(tag.messageCount))",
                              systemImage: viewModel.selectedTagId == tag.id ? "checkmark" : "")
                    }
                }
            }
            Section("演员") {
                Button {
                    Task { await viewModel.selectFilter(kind: .actor, id: 0) }
                } label: {
                    Label("无演员",
                          systemImage: viewModel.selectedActorId == 0 ? "checkmark" : "")
                }
                ForEach(viewModel.availableActors) { actor in
                    Button {
                        Task { await viewModel.selectFilter(kind: .actor, id: actor.id) }
                    } label: {
                        Label("\(actor.name) (\(actor.messageCount))",
                              systemImage: viewModel.selectedActorId == actor.id ? "checkmark" : "")
                    }
                }
            }
            Section("Issue") {
                Button {
                    Task { await viewModel.selectFilter(kind: .issue, id: 0) }
                } label: {
                    Label("无 issue",
                          systemImage: viewModel.selectedIssueId == 0 ? "checkmark" : "")
                }
                ForEach(viewModel.availableIssues) { issue in
                    Button {
                        Task { await viewModel.selectFilter(kind: .issue, id: issue.id) }
                    } label: {
                        Label(issue.title,
                              systemImage: viewModel.selectedIssueId == issue.id ? "checkmark" : "")
                    }
                }
            }
            if viewModel.selectedTagId != nil
                || viewModel.selectedActorId != nil
                || viewModel.selectedIssueId != nil {
                Divider()
                Button(role: .destructive) {
                    Task {
                        if viewModel.selectedTagId != nil {
                            await viewModel.selectFilter(kind: .tag, id: nil)
                        } else if viewModel.selectedActorId != nil {
                            await viewModel.selectFilter(kind: .actor, id: nil)
                        } else if viewModel.selectedIssueId != nil {
                            await viewModel.selectFilter(kind: .issue, id: nil)
                        }
                    }
                } label: {
                    Label("清除过滤", systemImage: "xmark.circle")
                }
            }
        } label: {
            HStack(spacing: 4) {
                Image(systemName: "line.3.horizontal.decrease.circle")
                if let _ = viewModel.selectedTagId
                    ?? viewModel.selectedActorId
                    ?? viewModel.selectedIssueId {
                    Text("已过滤")
                        .font(.system(size: 11))
                }
            }
        }
        .menuStyle(.borderlessButton)
        .fixedSize()
    }
}
