//
//  RepositoryManager.swift
//  MyNote
//
//  Repository 注册表 —— 把 (repo_id, 相对路径) 解析成本机绝对 URL。
//  Backend 端的 media.file_path 自 2026/06 起改为「相对挂载根」的 forward-slash 路径,
//  各端用各自的 repository 映射拼回绝对路径。
//
//  Mac 端的注册表持久化在 Settings.repositories(UserDefaults JSON)。
//  外接硬盘换盘符时,用户在「Repositories」设置面板手动改 path —— 不引入
//  Security-Scoped Bookmark(本 app 未开 sandbox,普通 path string 即可)。
//

import Foundation

@MainActor
final class RepositoryManager: ObservableObject {
    static let shared = RepositoryManager()

    @Published private(set) var repositories: RepoMap = [:]

    private init() {
        reload()
    }

    /// 从 UserDefaults 重读。在 onboarding / 设置面板修改后调用。
    func reload() {
        repositories = Settings.repositories
    }

    /// (repo_id, 相对路径) → 本机绝对 URL。
    /// 任一参数缺失 / repo 未注册 → 返回 nil(调用方走 fallback)。
    func resolve(repoId: String?, relativePath: String) -> URL? {
        guard let rid = repoId, let entry = repositories[rid] else { return nil }
        let root = URL(fileURLWithPath: entry.path, isDirectory: true)
        if relativePath.isEmpty { return root }
        // 相对路径在 backend 永远 forward-slash,URL.appendingPathComponent 在 macOS 上能直接处理
        return root.appendingPathComponent(relativePath)
    }

    /// repo 是否当前可用 —— mount 路径存在且是目录。
    /// 用来决定 UI 是显示文件还是「请插入 XX 硬盘」占位。
    func isAvailable(repoId: String?) -> Bool {
        guard let rid = repoId, let entry = repositories[rid] else { return false }
        var isDir: ObjCBool = false
        let exists = FileManager.default.fileExists(atPath: entry.path, isDirectory: &isDir)
        return exists && isDir.boolValue
    }

    /// UI 显示名:humanName 优先;空则用 repo_id;再空用「default」。
    func displayName(repoId: String?) -> String {
        guard let rid = repoId else { return "default" }
        if let name = repositories[rid]?.humanName, !name.isEmpty {
            return name
        }
        return rid
    }

    // MARK: - Mutation API(设置面板用)

    func set(repoId: String, path: String, humanName: String?) {
        var map = repositories
        map[repoId] = RepoEntry(path: path, humanName: humanName)
        Settings.repositories = map
        repositories = map
    }

    func remove(repoId: String) {
        var map = repositories
        map.removeValue(forKey: repoId)
        Settings.repositories = map
        repositories = map
    }
}
