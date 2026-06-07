//
//  APIClient.swift
//  MyNote
//
//  网络层，处理所有 API 调用
//

import Foundation
import Combine

class APIClient: ObservableObject {
    // API 基础 URL
    private let baseURL = "http://127.0.0.1:8002"
    
    // URLSession
    private let session: URLSession
    
    init() {
        let config = URLSessionConfiguration.default
        config.timeoutIntervalForRequest = 30
        config.timeoutIntervalForResource = 300
        self.session = URLSession(configuration: config)
    }
    
    // MARK: - Messages
    
    /// 获取消息 Feed，支持光标分页
    /// - Parameters:
    ///   - cursor: 分页光标（ISO 格式的时间戳），为 nil 则从最新开始
    ///   - limit: 单页数量，默认 20
    /// - Returns: MessageCursorResponse
    func getMessages(cursor: String? = nil, limit: Int = 20) async throws -> MessageCursorResponse {
        var components = URLComponents(string: "\(baseURL)/messages/with-detail")!
        var queryItems: [URLQueryItem] = [
            URLQueryItem(name: "limit", value: String(limit))
        ]
        
        if let cursor = cursor {
            queryItems.append(URLQueryItem(name: "cursor", value: cursor))
        }
        
        components.queryItems = queryItems
        
        guard let url = components.url else {
            throw APIError.invalidURL
        }
        
        print("📡 Fetching from: \(url.absoluteString)")
        
        do {
            let (data, response) = try await session.data(from: url)
            
            guard let httpResponse = response as? HTTPURLResponse else {
                throw APIError.invalidResponse
            }
            
            switch httpResponse.statusCode {
            case 200:
                let decoder = JSONDecoder()
                return try decoder.decode(MessageCursorResponse.self, from: data)
            default:
                let errorResponse = try? JSONDecoder().decode(ErrorResponse.self, from: data)
                throw APIError.serverError(errorResponse?.detail ?? "Unknown error")
            }
        } catch is URLError {
            throw APIError.networkError("无法连接到服务器: \(baseURL)\n请确保：\n1. 后端服务在运行\n2. 网络连接正常\n3. 没有代理/VPN 干扰")
        } catch {
            throw error
        }
    }
    
    /// 获取消息详情
    func getMessage(id: Int) async throws -> Message {
        let url = URL(string: "\(baseURL)/messages/\(id)")!
        let (data, response) = try await session.data(from: url)
        
        guard let httpResponse = response as? HTTPURLResponse, httpResponse.statusCode == 200 else {
            throw APIError.invalidResponse
        }
        
        return try JSONDecoder().decode(Message.self, from: data)
    }
    
    /// 创建消息
    func createMessage(text: String, mediaIds: [Int] = [], tagIds: [Int] = []) async throws -> Message {
        let url = URL(string: "\(baseURL)/messages")!
        
        var request = URLRequest(url: url)
        request.httpMethod = "POST"
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        
        let payload: [String: Any] = [
            "text": text,
            "files": [],
            "tag_ids": tagIds
        ]
        
        request.httpBody = try JSONSerialization.data(withJSONObject: payload)
        
        let (data, response) = try await session.data(for: request)
        
        guard let httpResponse = response as? HTTPURLResponse, httpResponse.statusCode == 201 else {
            throw APIError.invalidResponse
        }
        
        return try JSONDecoder().decode(Message.self, from: data)
    }
    
    /// 更新消息
    func updateMessage(id: Int, text: String? = nil, tagIds: [Int]? = nil) async throws -> Message {
        let url = URL(string: "\(baseURL)/messages/\(id)")!
        
        var request = URLRequest(url: url)
        request.httpMethod = "PUT"
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        
        var payload: [String: Any] = [:]
        if let text = text {
            payload["text"] = text
        }
        if let tagIds = tagIds {
            payload["tag_ids"] = tagIds
        }
        
        request.httpBody = try JSONSerialization.data(withJSONObject: payload)
        
        let (data, response) = try await session.data(for: request)
        
        guard let httpResponse = response as? HTTPURLResponse, httpResponse.statusCode == 200 else {
            throw APIError.invalidResponse
        }
        
        return try JSONDecoder().decode(Message.self, from: data)
    }
    
    /// 删除消息
    func deleteMessage(id: Int) async throws {
        let url = URL(string: "\(baseURL)/messages/\(id)")!
        
        var request = URLRequest(url: url)
        request.httpMethod = "DELETE"
        
        let (_, response) = try await session.data(for: request)
        
        guard let httpResponse = response as? HTTPURLResponse, httpResponse.statusCode == 204 else {
            throw APIError.invalidResponse
        }
    }
    
    // MARK: - Media
    
    /// 获取媒体库，支持光标分页
    /// - Parameters:
    ///   - cursor: 分页光标，格式为 "created_at|id"
    ///   - limit: 单页数量，默认 20
    ///   - type: 媒体类型过滤，"video" 或 "image"
    ///   - starred: 是否只显示已收藏
    /// - Returns: MediaCursorResponse
    func getMedia(cursor: String? = nil, limit: Int = 20, type: String? = nil, starred: Bool? = nil) async throws -> MediaCursorResponse {
        var components = URLComponents(string: "\(baseURL)/media")!
        var queryItems: [URLQueryItem] = [
            URLQueryItem(name: "limit", value: String(limit))
        ]
        
        if let cursor = cursor {
            queryItems.append(URLQueryItem(name: "cursor", value: cursor))
        }
        
        if let type = type {
            queryItems.append(URLQueryItem(name: "type", value: type))
        }
        
        if let starred = starred {
            queryItems.append(URLQueryItem(name: "starred", value: starred ? "true" : "false"))
        }
        
        components.queryItems = queryItems
        
        guard let url = components.url else {
            throw APIError.invalidURL
        }
        
        print("📡 Fetching media from: \(url.absoluteString)")
        
        do {
            let (data, response) = try await session.data(from: url)
            
            guard let httpResponse = response as? HTTPURLResponse else {
                throw APIError.invalidResponse
            }
            
            switch httpResponse.statusCode {
            case 200:
                let decoder = JSONDecoder()
                return try decoder.decode(MediaCursorResponse.self, from: data)
            default:
                let errorResponse = try? JSONDecoder().decode(ErrorResponse.self, from: data)
                throw APIError.serverError(errorResponse?.detail ?? "Unknown error")
            }
        } catch is URLError {
            throw APIError.networkError("无法连接到服务器: \(baseURL)\n请确保：\n1. 后端服务在运行\n2. 网络连接正常\n3. 没有代理/VPN 干扰")
        } catch {
            throw error
        }
    }
    
    /// 获取媒体详情
    func getMediaById(id: Int) async throws -> Media {
        let url = URL(string: "\(baseURL)/media/\(id)")!
        let (data, response) = try await session.data(from: url)
        
        guard let httpResponse = response as? HTTPURLResponse, httpResponse.statusCode == 200 else {
            throw APIError.invalidResponse
        }
        
        return try JSONDecoder().decode(Media.self, from: data)
    }
    
    /// 切换媒体收藏状态
    func toggleMediaStarred(id: Int) async throws -> Media {
        let url = URL(string: "\(baseURL)/media/\(id)/starred")!

        var request = URLRequest(url: url)
        request.httpMethod = "POST"

        let (data, response) = try await session.data(for: request)

        guard let httpResponse = response as? HTTPURLResponse, httpResponse.statusCode == 200 else {
            throw APIError.invalidResponse
        }

        return try JSONDecoder().decode(Media.self, from: data)
    }

    /// 获取媒体时间线(按日期分组统计)。
    func getMediaTimeline(type: String? = nil, starred: Bool? = nil) async throws -> [TimelineEntry] {
        var components = URLComponents(string: "\(baseURL)/media/timeline")!
        var queryItems: [URLQueryItem] = []

        if let type = type {
            queryItems.append(URLQueryItem(name: "type", value: type))
        }
        if let starred = starred {
            queryItems.append(URLQueryItem(name: "starred", value: starred ? "true" : "false"))
        }
        if !queryItems.isEmpty {
            components.queryItems = queryItems
        }

        guard let url = components.url else {
            throw APIError.invalidURL
        }

        let (data, response) = try await session.data(from: url)
        guard let httpResponse = response as? HTTPURLResponse, httpResponse.statusCode == 200 else {
            throw APIError.invalidResponse
        }
        return try JSONDecoder().decode([TimelineEntry].self, from: data)
    }
    
    // MARK: - Error Handling
    
    enum APIError: LocalizedError {
        case invalidURL
        case invalidResponse
        case serverError(String)
        case decodingError(String)
        case networkError(String)
        
        var errorDescription: String? {
            switch self {
            case .invalidURL:
                return "无效的 URL"
            case .invalidResponse:
                return "服务器响应错误"
            case .serverError(let message):
                return "服务器错误: \(message)"
            case .decodingError(let message):
                return "数据解析失败: \(message)"
            case .networkError(let message):
                return "网络错误: \(message)"
            }
        }
    }
}
