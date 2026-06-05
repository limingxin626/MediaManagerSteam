//
//  ContentView.swift
//  MyNote
//
//  第一期只保留媒体库 tab,FeedView 已下线。
//

import SwiftUI

struct ContentView: View {
    var body: some View {
        MediaLibraryView()
            .toolbar {
                ToolbarItem(placement: .automatic) {
                    Button(action: changeDataRoot) {
                        Label("更换数据目录", systemImage: "folder.badge.gearshape")
                    }
                }
            }
    }

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
    ContentView()
}
