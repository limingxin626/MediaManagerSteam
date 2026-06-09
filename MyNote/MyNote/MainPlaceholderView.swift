//
//  HomePlaceholderView.swift
//  MyNote
//
//  主页 tab 的占位实现 —— 后续接入首页仪表盘时整体替换本文件即可。
//  与 MessagesPlaceholderView 保持同构(居中 icon + 标题 + 「敬请期待」),
//  避免空白页面被误以为是 bug。
//

import SwiftUI

struct HomePlaceholderView: View {
    var body: some View {
        VStack(spacing: 12) {
            Image(systemName: AppTab.home.systemImage)
                .font(.system(size: 64))
                .foregroundColor(.secondary)
            Text(AppTab.home.title)
                .font(.title)
            Text("敬请期待")
                .font(.subheadline)
                .foregroundColor(.secondary)
        }
        .frame(maxWidth: .infinity, maxHeight: .infinity)
        .navigationTitle(AppTab.home.title)
    }
}

#Preview {
    HomePlaceholderView()
}
