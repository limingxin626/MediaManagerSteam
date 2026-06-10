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
//  Toolbar 统一在这一层挂(`.toolbar { toolbarContent }`),根据 selectedTab switch
//  路由到各 page 的 static 工厂。**不能让各 page 自己挂 .toolbar**:macOS 上 NSToolbar
//  是 Window 级单例,ZStack 同时持多个 NavigationStack 时,只要它们各自挂了 .toolbar,
//  AppKit 就会把所有 toolbar 内容合并显示 —— opacity=0 只挡 view body,不影响 toolbar
//  合并。上提到本层后单一来源,自然只有当前 tab 那一套。
//

import SwiftUI

struct ContentView: View {
    @State private var selectedTab: AppTab? = .home
    @StateObject private var mediaLibraryViewModel = MediaLibraryViewModel()
    @StateObject private var messagesViewModel = MessagesViewModel()

    /// 主窗口 detail 区域可用宽度。原本由 MessagesView 内部 GeometryReader 算,
    /// 上提到这里是因为 toolbar 上提后 —— MessagesView toolbar 的窄屏 fallback
    /// (FilterMenuCompact)需要这个宽度判断,而 toolbar 在 ContentView 里挂,
    /// 必须在 ContentView 也能拿到 width。同时 MessagesView 自己的内容布局
    /// (FilterSidebar 折叠)也用这同一个值,避免两边判断条件分裂。
    @State private var containerWidth: CGFloat = 1200

    var body: some View {
        NavigationSplitView {
            SidebarView(selection: $selectedTab)
        } detail: {
            GeometryReader { geo in
                detailContent
                    .onAppear { containerWidth = geo.size.width }
                    .onChange(of: geo.size.width) { _, new in containerWidth = new }
                    .toolbar { toolbarContent }
            }
        }
    }

    @ViewBuilder
    private var detailContent: some View {
        ZStack {
            HomePlaceholderView()
                .opacity(selectedTab == .home ? 1 : 0)
                .allowsHitTesting(selectedTab == .home)
            MessagesView(viewModel: messagesViewModel, containerWidth: containerWidth)
                .opacity(selectedTab == .messages ? 1 : 0)
                .allowsHitTesting(selectedTab == .messages)
            MediaLibraryView(viewModel: mediaLibraryViewModel)
                .opacity(selectedTab == .media ? 1 : 0)
                .allowsHitTesting(selectedTab == .media)
        }
        .frame(maxWidth: .infinity, maxHeight: .infinity)
    }

    /// 顶栏单一来源 —— 根据当前 tab 路由到对应 page 的 static 工厂。
    /// 之所以一定要 switch 路由而不是各 page 自己挂 .toolbar,见文件头注释。
    @ToolbarContentBuilder
    private var toolbarContent: some ToolbarContent {
        switch selectedTab {
        case .messages:
            MessagesView.messagesToolbar(
                viewModel: messagesViewModel,
                containerWidth: containerWidth
            )
        case .media:
            MediaLibraryView.mediaToolbar(viewModel: mediaLibraryViewModel)
        default:
            // home tab + nil:无 toolbar 内容。ToolbarContentBuilder 不接受
            // EmptyView 也不接受裸 nil,挂一个空 ToolbarItem 占位,视觉上不可见。
            ToolbarItem(placement: .automatic) { EmptyView() }
        }
    }
}

#Preview {
    ContentView()
}
