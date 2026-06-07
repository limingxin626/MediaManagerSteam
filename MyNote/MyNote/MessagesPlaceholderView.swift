//
//  MessagesPlaceholderView.swift
//  MyNote
//
//  消息 tab 的占位实现 —— 后续接入 message feed / actor 列表时整体替换本文件即可。
//  与 HomePlaceholderView 保持同构。
//

import SwiftUI

struct MessagesPlaceholderView: View {
    var body: some View {
        VStack(spacing: 12) {
            Image(systemName: AppTab.messages.systemImage)
                .font(.system(size: 64))
                .foregroundColor(.secondary)
            Text(AppTab.messages.title)
                .font(.title)
            Text("敬请期待")
                .font(.subheadline)
                .foregroundColor(.secondary)
        }
        .frame(maxWidth: .infinity, maxHeight: .infinity)
        .navigationTitle(AppTab.messages.title)
    }
}

#Preview {
    MessagesPlaceholderView()
}
