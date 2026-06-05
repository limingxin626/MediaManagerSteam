//
//  RepositoryManager.swift
//  MyNote
//
//  Repository 注册表 —— 把 (repo_id, 相对路径) 解析成本机绝对 URL。
//  Backend 端的 media.file_path 自 2026/06 起改为「相对挂载根」的 forward-slash 路径,
//  各端用各自的 repository 映射拼回绝对路径。
//
//  注册表来源:`<DATA_ROOT>/repositories.json` —— 跟 backend 共享同一份文件,
//  Mac 端只读 paths.darwin 段。外接硬盘换盘符时,直接编辑 JSON 文件即可。
//

import Foundation

/// 解析自 repositories.json 的单个 repo 条目(Mac 端只关心 darwin 路径)。
struct RepoEntry: Equatable {
    let path: String
    let humanName: String?
}

typealias RepoMap = [String: RepoEntry]

@MainActor
final class RepositoryManager: ObservableObject {
    static let shared = RepositoryManager()

    @Published private(set) var repositories: RepoMap = [:]
    /// 最近一次 reload 的错误描述(JSON 缺失 / 解析失败 / 当前平台无路径等)。
    /// 设置面板可显示;调用方一般忽略,UI 走 isAvailable 兜底。
    @Published private(set) var lastLoadError: String?

    private static let filename = "repositories.json"

    private init() {}

    /// 从 `<dataRoot>/repositories.json` 重读。app 启动 / 切换 dataRoot 后调用。
    /// dataRoot 为 nil 或文件缺失 → 把 repositories 置空,UI 走老路径兜底。
    func reload(dataRoot: URL?) {
        guard let dataRoot else {
            repositories = [:]
            lastLoadError = "DATA_ROOT 未配置"
            return
        }
        let url = dataRoot.appendingPathComponent(Self.filename)
        do {
            repositories = try Self.load(from: url)
            lastLoadError = nil
        } catch {
            repositories = [:]
            lastLoadError = error.localizedDescription
        }
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

    // MARK: - JSON 解析

    /// JSON schema 校验失败 / IO 异常 / 当前平台缺路径都抛 RepositoryLoadError。
    static func load(from fileURL: URL) throws -> RepoMap {
        let data: Data
        do {
            data = try Data(contentsOf: fileURL)
        } catch {
            throw RepositoryLoadError.fileMissing(fileURL.path)
        }
        let raw: RepositoriesFileV1
        do {
            raw = try JSONDecoder().decode(RepositoriesFileV1.self, from: data)
        } catch {
            throw RepositoryLoadError.parseFailed(error.localizedDescription)
        }
        guard raw.version == 1 else {
            throw RepositoryLoadError.unsupportedVersion(raw.version)
        }
        var out: RepoMap = [:]
        for (rid, entry) in raw.repositories {
            guard let darwinPath = entry.paths.darwin, !darwinPath.isEmpty else {
                // 静默跳过没有 darwin 路径的 repo —— 对应文件落不到本机,
                // UI 上 resolve 会返 nil 进 fallback。不视作整个文件解析失败。
                continue
            }
            out[rid] = RepoEntry(path: darwinPath, humanName: entry.humanName)
        }
        return out
    }
}

enum RepositoryLoadError: LocalizedError {
    case fileMissing(String)
    case parseFailed(String)
    case unsupportedVersion(Int)

    var errorDescription: String? {
        switch self {
        case .fileMissing(let p): return "repositories.json 不存在: \(p)"
        case .parseFailed(let m): return "repositories.json 解析失败: \(m)"
        case .unsupportedVersion(let v): return "repositories.json 版本不支持: \(v)"
        }
    }
}

// MARK: - JSON 解码模型(只在本文件内部用)

private struct RepositoriesFileV1: Decodable {
    let version: Int
    let defaultRepoId: String
    let repositories: [String: RepoEntryJSON]

    enum CodingKeys: String, CodingKey {
        case version
        case defaultRepoId = "default_repo_id"
        case repositories
    }
}

private struct RepoEntryJSON: Decodable {
    let humanName: String?
    let paths: RepoPathsJSON

    enum CodingKeys: String, CodingKey {
        case humanName = "human_name"
        case paths
    }
}

private struct RepoPathsJSON: Decodable {
    let windows: String?
    let darwin: String?
    let linux: String?
}
