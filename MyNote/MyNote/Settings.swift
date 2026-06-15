//
//  Settings.swift
//  MyNote
//
//  应用配置 - 持久化用户偏好到 UserDefaults
//

import Foundation

/// 全局设置访问入口。所有配置项都用单例 + 计算属性的形式暴露,内部走 UserDefaults。
///
/// Repository 映射不在这里 —— 它存在 `<DATA_ROOT>/repositories.json`,由
/// `RepositoryManager` 在 app 启动 / dataRoot 切换时读取。
enum Settings {
    private static let dataRootKey = "dataRoot"

    /// 数据根目录。指向一份兼容 backend schema 的目录,包含:
    /// - `db.sqlite3`            共享 SQLite 数据库
    /// - `thumbs/{id}.webp`      缩略图
    /// - `repositories.json`     repo 注册表(Backend + Mac 共享)
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
}
