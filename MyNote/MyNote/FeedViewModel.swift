//
//  FeedViewModel.swift
//  MyNote
//
//  Feed 数据模型，管理消息列表和分页
//

import Foundation
import Combine

class FeedViewModel: ObservableObject {
    @Published var messages: [Message] = []
    @Published var isLoading = false
    @Published var isLoadingMore = false
    @Published var errorMessage: String? = nil
    @Published var nextCursor: String? = nil
    @Published var hasMore = false
    
    private let apiClient: APIClient
    
    init(apiClient: APIClient = APIClient()) {
        self.apiClient = apiClient
    }
    
    // MARK: - Feed 操作
    
    /// 加载初始 Feed（从最新开始）
    func loadInitial() async {
        await MainActor.run {
            isLoading = true
            errorMessage = nil
        }
        
        do {
            let response = try await apiClient.getMessages(cursor: nil, limit: 20)
            await MainActor.run {
                messages = response.items
                nextCursor = response.nextCursor
                hasMore = response.hasMore
                isLoading = false
            }
        } catch {
            await MainActor.run {
                errorMessage = error.localizedDescription
                isLoading = false
            }
        }
    }
    
    /// 加载更多（向下翻页）
    func loadMore() async {
        guard !isLoadingMore && hasMore && nextCursor != nil else { return }
        
        await MainActor.run {
            isLoadingMore = true
        }
        
        do {
            let response = try await apiClient.getMessages(cursor: nextCursor, limit: 20)
            await MainActor.run {
                messages.append(contentsOf: response.items)
                nextCursor = response.nextCursor
                hasMore = response.hasMore
                isLoadingMore = false
            }
        } catch {
            await MainActor.run {
                errorMessage = error.localizedDescription
                isLoadingMore = false
            }
        }
    }
    
    /// 刷新 Feed（从最新开始）
    func refresh() async {
        await MainActor.run {
            isLoading = true
            errorMessage = nil
        }
        
        do {
            let response = try await apiClient.getMessages(cursor: nil, limit: 20)
            await MainActor.run {
                messages = response.items
                nextCursor = response.nextCursor
                hasMore = response.hasMore
                isLoading = false
            }
        } catch {
            await MainActor.run {
                errorMessage = error.localizedDescription
                isLoading = false
            }
        }
    }
    
    // MARK: - 消息操作
    
    /// 创建新消息
    func createMessage(text: String) async {
        do {
            let newMessage = try await apiClient.createMessage(text: text)
            await MainActor.run {
                messages.insert(newMessage, at: 0)
            }
        } catch {
            await MainActor.run {
                errorMessage = error.localizedDescription
            }
        }
    }
    
    /// 删除消息
    func deleteMessage(id: Int) async {
        do {
            try await apiClient.deleteMessage(id: id)
            await MainActor.run {
                messages.removeAll { $0.id == id }
            }
        } catch {
            await MainActor.run {
                errorMessage = error.localizedDescription
            }
        }
    }
    
    /// 更新消息
    func updateMessage(id: Int, text: String) async {
        do {
            let updatedMessage = try await apiClient.updateMessage(id: id, text: text)
            await MainActor.run {
                if let index = messages.firstIndex(where: { $0.id == id }) {
                    messages[index] = updatedMessage
                }
            }
        } catch {
            await MainActor.run {
                errorMessage = error.localizedDescription
            }
        }
    }
}
