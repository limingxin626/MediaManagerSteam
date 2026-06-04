//
//  FeedView.swift
//  MyNote
//
//  消息 Feed 视图
//

import SwiftUI

struct FeedView: View {
    @StateObject private var viewModel = FeedViewModel()
    @State private var newMessageText = ""
    @State private var showNewMessageSheet = false
    
    var body: some View {
        ZStack {
            VStack(spacing: 0) {
                // 头部
                HStack {
                    Text("消息")
                        .font(.largeTitle)
                        .fontWeight(.bold)
                    
                    Spacer()
                    
                    Button(action: { showNewMessageSheet = true }) {
                        Image(systemName: "square.and.pencil")
                            .font(.system(size: 16))
                            .foregroundColor(.blue)
                    }
                }
                .padding()
                
                // Feed 列表
                if viewModel.isLoading {
                    VStack {
                        Spacer()
                        ProgressView()
                        Spacer()
                    }
                } else if viewModel.messages.isEmpty {
                    VStack {
                        Spacer()
                        Text("暂无消息")
                            .foregroundColor(.secondary)
                        Spacer()
                    }
                } else {
                    ScrollView {
                        LazyVStack(spacing: 12) {
                            ForEach(viewModel.messages) { message in
                                MessageRow(message: message, viewModel: viewModel)
                            }
                            
                            // 加载更多
                            if viewModel.hasMore {
                                HStack {
                                    Spacer()
                                    if viewModel.isLoadingMore {
                                        ProgressView()
                                    } else {
                                        Button("加载更多") {
                                            Task {
                                                await viewModel.loadMore()
                                            }
                                        }
                                    }
                                    Spacer()
                                }
                                .padding()
                                .onAppear {
                                    Task {
                                        await viewModel.loadMore()
                                    }
                                }
                            }
                        }
                        .padding(.horizontal)
                        .padding(.top, 12)
                    }
                }
                
                Spacer()
            }
            
            // 错误提示
            if let error = viewModel.errorMessage {
                VStack {
                    HStack {
                        Text(error)
                            .foregroundColor(.red)
                        Spacer()
                        Button(action: { viewModel.errorMessage = nil }) {
                            Image(systemName: "xmark")
                        }
                    }
                    .padding()
                    .background(Color.red.opacity(0.1))
                    .cornerRadius(8)
                    .padding()
                    
                    Spacer()
                }
            }
        }
        .sheet(isPresented: $showNewMessageSheet) {
            NewMessageSheet(isPresented: $showNewMessageSheet, viewModel: viewModel)
        }
        .onAppear {
            Task {
                await viewModel.loadInitial()
            }
        }
        .refreshable {
            await viewModel.refresh()
        }
    }
}

// MARK: - Message Row

struct MessageRow: View {
    let message: Message
    let viewModel: FeedViewModel
    @State private var showDeleteConfirm = false
    
    var body: some View {
        VStack(alignment: .leading, spacing: 8) {
            // Actor 和日期
            HStack {
                VStack(alignment: .leading, spacing: 2) {
                    Text(message.actorName ?? "匿名")
                        .font(.headline)
                    Text(formatDate(message.createdAt))
                        .font(.caption)
                        .foregroundColor(.secondary)
                }
                
                Spacer()
                
                Menu {
                    Button(role: .destructive) {
                        showDeleteConfirm = true
                    } label: {
                        Label("删除", systemImage: "trash")
                    }
                } label: {
                    Image(systemName: "ellipsis")
                        .foregroundColor(.secondary)
                }
            }
            
            // 消息文本
            if let text = message.text {
                Text(text)
                    .lineLimit(nil)
                    .textSelection(.enabled)
            } else {
                Text("(无文本)")
                    .foregroundColor(.secondary)
            }
            
            // 标签
            if !message.tags.isEmpty {
                HStack(spacing: 8) {
                    ForEach(message.tags) { tag in
                        Text("#\(tag.name)")
                            .font(.caption)
                            .foregroundColor(.blue)
                            .padding(.horizontal, 8)
                            .padding(.vertical, 4)
                            .background(Color.blue.opacity(0.1))
                            .cornerRadius(4)
                    }
                }
            }
            
            // 媒体
            if !message.mediaItems.isEmpty {
                VStack(spacing: 8) {
                    ForEach(message.mediaItems) { mediaItem in
                        MediaThumbnail(mediaItem: mediaItem)
                    }
                }
            }
        }
        .padding()
        .background(Color.white)
        .cornerRadius(8)
        .overlay(
            RoundedRectangle(cornerRadius: 8)
                .stroke(Color.gray.opacity(0.2), lineWidth: 1)
        )
        .confirmationDialog("确认删除", isPresented: $showDeleteConfirm) {
            Button("删除", role: .destructive) {
                Task {
                    await viewModel.deleteMessage(id: message.id)
                }
            }
        } message: {
            Text("确定要删除这条消息吗？")
        }
    }
    
    private func formatDate(_ dateString: String) -> String {
        let formatter = ISO8601DateFormatter()
        if let date = formatter.date(from: dateString) {
            let dateFormatter = DateFormatter()
            dateFormatter.locale = Locale(identifier: "zh_CN")
            dateFormatter.dateFormat = "MM月dd日 HH:mm"
            return dateFormatter.string(from: date)
        }
        return dateString
    }
}

// MARK: - Media Thumbnail

struct MediaThumbnail: View {
    let mediaItem: MessageMediaItem
    
    var body: some View {
        VStack {
            if let mimeType = mediaItem.mimeType, mimeType.contains("image") {
                AsyncImage(url: URL(string: mediaItem.thumbUrl)) { phase in
                    switch phase {
                    case .empty:
                        ProgressView()
                    case .success(let image):
                        image
                            .resizable()
                            .scaledToFit()
                            .cornerRadius(4)
                    case .failure:
                        Image(systemName: "photo")
                            .foregroundColor(.gray)
                    @unknown default:
                        EmptyView()
                    }
                }
            } else if let mimeType = mediaItem.mimeType, mimeType.contains("video") {
                ZStack {
                    AsyncImage(url: URL(string: mediaItem.thumbUrl)) { phase in
                        switch phase {
                        case .empty:
                            ProgressView()
                        case .success(let image):
                            image
                                .resizable()
                                .scaledToFit()
                                .cornerRadius(4)
                        case .failure:
                            Rectangle()
                                .foregroundColor(.gray)
                                .cornerRadius(4)
                        @unknown default:
                            EmptyView()
                        }
                    }
                    
                    Image(systemName: "play.circle.fill")
                        .font(.system(size: 40))
                        .foregroundColor(.white)
                }
            } else {
                HStack {
                    Image(systemName: "doc")
                        .foregroundColor(.gray)
                    Text(mediaItem.filePath.components(separatedBy: "/").last ?? "文件")
                        .font(.caption)
                        .lineLimit(1)
                }
                .padding()
                .background(Color(.gray).opacity(0.1))
                .cornerRadius(4)
            }
        }
    }
}

// MARK: - New Message Sheet

struct NewMessageSheet: View {
    @Binding var isPresented: Bool
    let viewModel: FeedViewModel
    @State private var messageText = ""
    @State private var isSubmitting = false
    
    var body: some View {
        NavigationView {
            VStack(spacing: 12) {
                TextEditor(text: $messageText)
                    .frame(minHeight: 100)
                    .padding()
                    .background(Color(.gray).opacity(0.1))
                    .cornerRadius(8)
                    .padding()
                
                Spacer()
                
                HStack(spacing: 12) {
                    Button("取消") {
                        isPresented = false
                    }
                    
                    Spacer()
                    
                    Button(action: submitMessage) {
                        if isSubmitting {
                            ProgressView()
                        } else {
                            Text("发布")
                        }
                    }
                    .disabled(messageText.trimmingCharacters(in: .whitespaces).isEmpty || isSubmitting)
                }
                .padding()
            }
            .navigationTitle("新消息")
        }
    }
    
    private func submitMessage() {
        isSubmitting = true
        Task {
            await viewModel.createMessage(text: messageText)
            isPresented = false
            isSubmitting = false
        }
    }
}

#Preview {
    FeedView()
}
