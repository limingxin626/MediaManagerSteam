//
//  ContentView.swift
//  MyNote
//
//  主窗口 = NavigationSplitView(sidebar: SidebarView, detail: 当前 tab 内容)。
//  SidebarView 选中态由 ContentView 持有;各 tab 的 ViewModel 也由 ContentView 持有,
//  保证切到其他 tab 再切回时不会因为 view 重建而丢失滚动位置/筛选条件/选中消息。
//
//  实现:detail 区域用 ZStack 同时持三个 tab 的 view,通过 opacity + allowsHitTesting
//  控制可见性(mac-media-page-state-and-styling 决策)。三个 ViewModel 用 @StateObject
//  一次性创建,生命周期 = ContentView 生命周期。
//

import SwiftUI

struct ContentView: View {
    @State private var selectedTab: AppTab? = .home
    @StateObject private var mediaLibraryViewModel = MediaLibraryViewModel()
    @StateObject private var messagesViewModel = MessagesViewModel()

    var body: some View {
        NavigationSplitView {
            SidebarView(selection: $selectedTab)
        } detail: {
            detailContent
        }
    }

    @ViewBuilder
    private var detailContent: some View {
        ZStack {
            HomePlaceholderView()
                .opacity(selectedTab == .home ? 1 : 0)
                .allowsHitTesting(selectedTab == .home)
            MessagesView(viewModel: messagesViewModel)
                .opacity(selectedTab == .messages ? 1 : 0)
                .allowsHitTesting(selectedTab == .messages)
            MediaLibraryView(viewModel: mediaLibraryViewModel)
                .opacity(selectedTab == .media ? 1 : 0)
                .allowsHitTesting(selectedTab == .media)
        }
        .frame(maxWidth: .infinity, maxHeight: .infinity)
    }
}

#Preview {
    ContentView()
}
