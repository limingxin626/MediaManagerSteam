//
//  MediaLibraryViewModel.swift
//  MyNote
//
//  媒体库数据模型，管理媒体列表和分页
//

import Foundation
import Combine

class MediaLibraryViewModel: ObservableObject {
    @Published var media: [Media] = []
    @Published var isLoading = false
    @Published var isLoadingMore = false
    @Published var errorMessage: String? = nil
    @Published var nextCursor: String? = nil
    @Published var hasMore = false
    @Published var selectedMediaType: String? = nil  // nil (全部), "image", "video"
    @Published var showOnlyStarred = false
    
    private let apiClient: APIClient
    
    init(apiClient: APIClient = APIClient()) {
        self.apiClient = apiClient
    }
    
    // MARK: - 媒体库操作
    
    /// 加载初始媒体库（从最新开始）
    func loadInitial() async {
        await MainActor.run {
            isLoading = true
            errorMessage = nil
        }
        
        do {
            let response = try await apiClient.getMedia(
                cursor: nil,
                limit: 40,
                type: selectedMediaType,
                starred: showOnlyStarred ? true : nil
            )
            await MainActor.run {
                media = response.items
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
            let response = try await apiClient.getMedia(
                cursor: nextCursor,
                limit: 40,
                type: selectedMediaType,
                starred: showOnlyStarred ? true : nil
            )
            await MainActor.run {
                media.append(contentsOf: response.items)
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
    
    /// 刷新媒体库（从最新开始）
    func refresh() async {
        await MainActor.run {
            isLoading = true
            errorMessage = nil
        }
        
        do {
            let response = try await apiClient.getMedia(
                cursor: nil,
                limit: 40,
                type: selectedMediaType,
                starred: showOnlyStarred ? true : nil
            )
            await MainActor.run {
                media = response.items
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
    
    /// 改变媒体类型过滤
    func changeMediaType(_ type: String?) async {
        await MainActor.run {
            selectedMediaType = type
        }
        await loadInitial()
    }
    
    /// 切换"仅显示收藏"过滤
    func toggleStarredOnly() async {
        await MainActor.run {
            showOnlyStarred.toggle()
        }
        await loadInitial()
    }
    
    // MARK: - 媒体操作
    
    /// 切换媒体收藏状态
    func toggleMediaStarred(id: Int) async {
        do {
            let updated = try await apiClient.toggleMediaStarred(id: id)
            
            await MainActor.run {
                if let index = media.firstIndex(where: { $0.id == id }) {
                    media[index] = updated
                }
            }
        } catch {
            await MainActor.run {
                errorMessage = error.localizedDescription
            }
        }
    }
}
