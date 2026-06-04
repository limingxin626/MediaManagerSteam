//
//  LocalDatabase.swift
//  MyNote
//
//  GRDB 只读连接管理。整个 app 共享一个 DatabaseQueue。
//

import Foundation
import GRDB

/// DATA_ROOT 校验/连接失败的具体原因。UI 层据此显示对应提示。
enum DataRootError: LocalizedError {
    case directoryMissing(URL)
    case databaseFileMissing(URL)
    case schemaMismatch(String)
    case openFailed(String)

    var errorDescription: String? {
        switch self {
        case .directoryMissing(let url):
            return "数据目录不存在: \(url.path)"
        case .databaseFileMissing(let url):
            return "未找到数据库文件: \(url.path)"
        case .schemaMismatch(let detail):
            return "数据库格式不兼容: \(detail)"
        case .openFailed(let detail):
            return "打开数据库失败: \(detail)"
        }
    }
}

final class LocalDatabase {
    static let shared = LocalDatabase()

    private(set) var queue: DatabaseQueue?
    private(set) var rootURL: URL?

    private init() {}

    /// 校验 + 打开。成功后 `queue` 与 `rootURL` 都会被赋值。
    /// 失败时抛 `DataRootError`,内部状态不变。
    func open(rootURL: URL) throws {
        try Self.validate(rootURL: rootURL)

        let dbURL = rootURL.appendingPathComponent("db.sqlite3")
        var config = Configuration()
        config.readonly = true

        do {
            let newQueue = try DatabaseQueue(path: dbURL.path, configuration: config)
            // 关掉旧连接(若有)
            self.queue = newQueue
            self.rootURL = rootURL
        } catch {
            throw DataRootError.openFailed(error.localizedDescription)
        }
    }

    /// 关闭连接,清空状态。用户切换 DATA_ROOT 时先调它。
    func close() {
        queue = nil
        rootURL = nil
    }

    /// 校验目录布局与 schema 兼容性。不持有连接;成功不代表已 open。
    static func validate(rootURL: URL) throws {
        let fm = FileManager.default
        var isDir: ObjCBool = false
        guard fm.fileExists(atPath: rootURL.path, isDirectory: &isDir), isDir.boolValue else {
            throw DataRootError.directoryMissing(rootURL)
        }

        let dbURL = rootURL.appendingPathComponent("db.sqlite3")
        guard fm.fileExists(atPath: dbURL.path) else {
            throw DataRootError.databaseFileMissing(dbURL)
        }

        // 用临时只读连接做一次 schema 探测,避免污染 shared 状态
        var config = Configuration()
        config.readonly = true
        do {
            let probe = try DatabaseQueue(path: dbURL.path, configuration: config)
            try probe.read { db in
                _ = try Int.fetchOne(db, sql: "SELECT 1 FROM media LIMIT 1")
            }
        } catch let error as DataRootError {
            throw error
        } catch {
            throw DataRootError.schemaMismatch(error.localizedDescription)
        }
    }
}
