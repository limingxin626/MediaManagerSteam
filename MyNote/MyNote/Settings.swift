//
//  Settings.swift
//  MyNote
//
//  应用配置 - 持久化用户偏好到 UserDefaults
//

import Foundation

/// 一个 media 仓库的元数据。`path` 是本机绝对路径(外接盘可能换盘符 → 用户在设置里改);
/// `humanName` 是 UI 显示名(为空时回退到 repo_id)。
struct RepoEntry: Codable, Equatable {
    var path: String
    var humanName: String?
}

typealias RepoMap = [String: RepoEntry]

/// 全局设置访问入口。所有配置项都用单例 + 计算属性的形式暴露,内部走 UserDefaults。
enum Settings {
    private static let dataRootKey = "dataRoot"
    private static let repositoriesKey = "repositories"
    private static let defaultRepoId = "uploads"

    /// 数据根目录。指向一份兼容 backend schema 的目录,包含:
    /// - `db.sqlite3`            共享 SQLite 数据库
    /// - `data/thumbs/{id}.webp` 缩略图
    /// - `uploads/YYYY/MM/DD/`   原始媒体文件(本身也是 default repo)
    ///
    /// 未配置时返回 nil,UI 层应引导用户走 onboarding。
    static var dataRoot: URL? {
        get {
            guard let path = UserDefaults.standard.string(forKey: dataRootKey), !path.isEmpty else {
                return nil
            }
            return URL(fileURLWithPath: path, isDirectory: true)
        }
        set {
            if let url = newValue {
                UserDefaults.standard.set(url.path, forKey: dataRootKey)
            } else {
                UserDefaults.standard.removeObject(forKey: dataRootKey)
            }
        }
    }

    /// {repo_id: RepoEntry} 注册表。**JSON-encoded Data** 存在 UserDefaults。
    /// 用 Data 而不是直接 plist dict,是为了将来给 RepoEntry 加字段时不破坏旧用户。
    static var repositories: RepoMap {
        get {
            guard let data = UserDefaults.standard.data(forKey: repositoriesKey) else { return [:] }
            return (try? JSONDecoder().decode(RepoMap.self, from: data)) ?? [:]
        }
        set {
            if newValue.isEmpty {
                UserDefaults.standard.removeObject(forKey: repositoriesKey)
            } else if let data = try? JSONEncoder().encode(newValue) {
                UserDefaults.standard.set(data, forKey: repositoriesKey)
            }
        }
    }

    /// 首次升级:repositories 为空 + dataRoot 已设 → 自动种 default repo = `<DATA_ROOT>/uploads`。
    /// backend 端 default repo id 是 basename(UPLOAD_DIR).lower(),典型为 "uploads";
    /// 如果用户的 backend `UPLOAD_DIR` basename 不是 uploads,需手动在 Repositories 设置里改。
    static func migrateLegacyDataRootIfNeeded() {
        guard repositories.isEmpty, let root = dataRoot else { return }
        let uploadsPath = root.appendingPathComponent("uploads", isDirectory: true).path
        repositories = [defaultRepoId: RepoEntry(path: uploadsPath, humanName: nil)]
    }
}
