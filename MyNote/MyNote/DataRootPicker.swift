//
//  DataRootPicker.swift
//  MyNote
//
//  封装 NSOpenPanel,让用户选择 DATA_ROOT 目录
//

import AppKit

enum DataRootPicker {
    /// 弹出系统目录选择面板,同步返回用户选中的目录;取消时返回 nil。
    /// 必须在主线程调用。
    @MainActor
    static func chooseDirectory(prompt: String = "选择 MediaManager 数据目录") -> URL? {
        let panel = NSOpenPanel()
        panel.title = prompt
        panel.message = "请选择包含 db.sqlite3 的数据根目录"
        panel.prompt = "选择"
        panel.canChooseDirectories = true
        panel.canChooseFiles = false
        panel.allowsMultipleSelection = false
        panel.canCreateDirectories = false

        let response = panel.runModal()
        guard response == .OK, let url = panel.url else { return nil }
        return url
    }
}
