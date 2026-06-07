//
//  SidebarView.swift
//  MyNote
//
//  主窗口左侧导航栏 —— 三个 tab 入口(主页/消息/媒体)+ 底部「更换数据目录」配置项。
//  与 ContentView 通过 `Binding<AppTab>` 共享当前选中态。
//

import SwiftUI
import AppKit

struct SidebarView: View {
    @Binding var selection: AppTab?

    var body: some View {
        VStack(spacing: 0) {
            // 顶部 tab 列表 —— List(selection:) 自带 macOS sidebar 风格 + 选中高亮
            // NavigationSplitView 范式下用 selection: + .tag 直接驱动,不再用
            // NavigationLink(否则会向 detail 导航栈 push 值,与 selection 双驱动)。
            List(selection: $selection) {
                ForEach(AppTab.allCases) { tab in
                    Label(tab.title, systemImage: tab.systemImage).tag(tab)
                }
            }
            .listStyle(.sidebar)
            .frame(maxHeight: .infinity)

            Divider()

            // 底部「更换数据目录」 —— 配置类操作,放在 sidebar 底部与 tab 分层
            Button(action: changeDataRoot) {
                Label("更换数据目录", systemImage: "folder.badge.gearshape")
                    .frame(maxWidth: .infinity, alignment: .leading)
            }
            .buttonStyle(.plain)
            .padding(.horizontal, 12)
            .padding(.vertical, 8)
        }
    }

    // MARK: - 更换数据目录

    @MainActor
    private func changeDataRoot() {
        guard let url = DataRootPicker.chooseDirectory(prompt: "更换数据目录") else { return }
        do {
            try LocalDatabase.validate(rootURL: url)
            LocalDatabase.shared.close()
            try LocalDatabase.shared.open(rootURL: url)
            Settings.dataRoot = url
            RepositoryManager.shared.reload(dataRoot: url)
            // 简单做法:重启 app 让所有 ViewModel 重建
            NSApplication.shared.terminate(nil)
        } catch {
            let alert = NSAlert()
            alert.messageText = "切换数据目录失败"
            alert.informativeText = error.localizedDescription
            alert.alertStyle = .warning
            alert.runModal()
        }
    }
}

#Preview {
    SidebarView(selection: .constant(.media as AppTab?))
}
