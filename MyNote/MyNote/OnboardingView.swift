//
//  OnboardingView.swift
//  MyNote
//
//  首次启动或 DATA_ROOT 失效时显示的引导界面。
//

import SwiftUI

struct OnboardingView: View {
    /// 用户成功选择并校验通过后回调,父级据此切换主界面。
    let onPicked: (URL) -> Void

    @State private var errorMessage: String?

    var body: some View {
        VStack(spacing: 20) {
            Image(systemName: "externaldrive.connected.to.line.below")
                .font(.system(size: 56))
                .foregroundColor(.accentColor)

            Text("欢迎使用 MyNote")
                .font(.title)
                .fontWeight(.bold)

            Text("请选择包含 db.sqlite3 的数据根目录")
                .font(.body)
                .foregroundColor(.secondary)
                .multilineTextAlignment(.center)

            Button(action: pick) {
                Label("选择数据目录", systemImage: "folder")
                    .padding(.horizontal, 8)
            }
            .controlSize(.large)
            .buttonStyle(.borderedProminent)

            if let errorMessage {
                Text(errorMessage)
                    .font(.caption)
                    .foregroundColor(.red)
                    .multilineTextAlignment(.center)
                    .padding(.horizontal, 32)
            }
        }
        .padding(40)
        .frame(minWidth: 480, minHeight: 360)
    }

    @MainActor
    private func pick() {
        guard let url = DataRootPicker.chooseDirectory() else { return }
        do {
            try LocalDatabase.validate(rootURL: url)
            Settings.dataRoot = url
            errorMessage = nil
            onPicked(url)
        } catch {
            errorMessage = error.localizedDescription
        }
    }
}
