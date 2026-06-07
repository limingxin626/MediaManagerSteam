//
//  MyNoteApp.swift
//  MyNote
//
//  App 入口 - 启动时校验 DATA_ROOT、打开本地数据库,失败进入引导界面。
//

import SwiftUI
import GRDB

@main
struct MyNoteApp: App {
    @State private var dbReady = false
    @State private var startupError: String?

    /// 跨窗口共享的预览会话 —— 主窗口和独立的全屏预览窗口都靠它通信。
    @StateObject private var previewSession = MediaPreviewSession()

    var body: some Scene {
        WindowGroup {
            Group {
                if dbReady {
                    ContentView()
                } else {
                    OnboardingView { _ in
                        // 用户选完目录,Settings.dataRoot 已写入,这里再 open 一次
                        tryOpen()
                    }
                    .overlay(alignment: .bottom) {
                        if let startupError {
                            Text(startupError)
                                .font(.caption)
                                .foregroundColor(.red)
                                .padding()
                        }
                    }
                }
            }
            .environmentObject(previewSession)
            .onAppear {
                tryOpen()
            }
        }

        // 独立的预览窗口(Photos.app 风格):双击网格 cell → openWindow(id:) 触发,
        // 在 view onAppear 时立刻进入 macOS 原生全屏。Window(非 WindowGroup) 天然
        // 单实例,重复 openWindow 只会把它前置 + 换内容,不会新开。
        Window("预览", id: "media-preview") {
            MediaPreviewWindowView()
                .environmentObject(previewSession)
        }
        .windowStyle(.hiddenTitleBar)
        .windowResizability(.contentSize)
    }

    @MainActor
    private func tryOpen() {
        guard let root = Settings.dataRoot else {
            dbReady = false
            return
        }
        do {
            try LocalDatabase.shared.open(rootURL: root)
            // repositories.json 在同一 DATA_ROOT 下,由 backend / 用户手写维护;Mac 端只读 darwin 段。
            RepositoryManager.shared.reload(dataRoot: root)
            // 校验性能轻量,顺带打印库大小用于诊断
            if let queue = LocalDatabase.shared.queue {
                let count = try queue.read { db in
                    try Int.fetchOne(db, sql: "SELECT COUNT(*) FROM media") ?? 0
                }
                print("✅ LocalDatabase opened. media count = \(count) at \(root.path)")
            }
            startupError = nil
            dbReady = true
        } catch {
            print("❌ LocalDatabase open failed: \(error.localizedDescription)")
            startupError = error.localizedDescription
            Settings.dataRoot = nil  // 清掉无效路径,下次进 onboarding
            dbReady = false
        }
    }
}
