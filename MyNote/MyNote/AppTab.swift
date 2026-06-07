//
//  AppTab.swift
//  MyNote
//
//  顶层 tab 导航的单一真源。SidebarView、ContentView 都以这个枚举驱动。
//  后续新增 tab 时只需在 case + title/systemImage switch 里追加,编译期保证 exhaustive。
//

import Foundation

enum AppTab: String, CaseIterable, Identifiable, Hashable {
    case home
    case messages
    case media

    var id: String { rawValue }

    /// 用户可见的中文标题。
    var title: String {
        switch self {
        case .home: return "主页"
        case .messages: return "消息"
        case .media: return "媒体"
        }
    }

    /// SF Symbol,sidebar 和占位页都共用,保证视觉一致。
    var systemImage: String {
        switch self {
        case .home: return "house"
        case .messages: return "bubble.left.and.bubble.right"
        case .media: return "photo.on.rectangle"
        }
    }
}
