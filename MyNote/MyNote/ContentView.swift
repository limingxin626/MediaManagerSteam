//
//  ContentView.swift
//  MyNote
//
//  主窗口 = NavigationSplitView(sidebar: SidebarView, detail: 当前 tab 内容)。
//  SidebarView 选中态由 ContentView 持有;媒体页的 ViewModel 也由 ContentView 持有,
//  保证切到其他 tab 再切回时不会因为 view 重建而丢失滚动位置/筛选条件。
//

import SwiftUI

struct ContentView: View {
    @State private var selectedTab: AppTab? = .media
    @StateObject private var mediaLibraryViewModel = MediaLibraryViewModel()

    var body: some View {
        NavigationSplitView {
            SidebarView(selection: $selectedTab)
        } detail: {
            detailContent
        }
    }

    @ViewBuilder
    private var detailContent: some View {
        switch selectedTab {
        case .home:
            HomePlaceholderView()
        case .messages:
            MessagesPlaceholderView()
        case .media:
            MediaLibraryView(viewModel: mediaLibraryViewModel)
        case .none:
            Text("请选择侧栏项目")
                .foregroundColor(.secondary)
                .frame(maxWidth: .infinity, maxHeight: .infinity)
        }
    }
}

#Preview {
    ContentView()
}
