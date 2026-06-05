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
            .onAppear {
                tryOpen()
            }
        }
    }

    private func tryOpen() {
        guard let root = Settings.dataRoot else {
            dbReady = false
            return
        }
        do {
            try LocalDatabase.shared.open(rootURL: root)
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
