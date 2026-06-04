//
//  MediaLibraryView.swift
//  MyNote
//
//  媒体库视图 - 网格展示所有媒体
//

import SwiftUI

struct MediaLibraryView: View {
    @StateObject private var viewModel = MediaLibraryViewModel()
    @State private var selectedMedia: Media? = nil
    @State private var showImageDetail = false
    
    let columns = [
        GridItem(.flexible(), spacing: 8),
        GridItem(.flexible(), spacing: 8),
        GridItem(.flexible(), spacing: 8),
        GridItem(.flexible(), spacing: 8)
    ]
    
    var body: some View {
        ZStack {
            VStack(spacing: 0) {
                // 头部 - 标题和过滤
                VStack(spacing: 12) {
                    HStack {
                        Text("媒体库")
                            .font(.largeTitle)
                            .fontWeight(.bold)
                        
                        Spacer()
                        
                        Button(action: { Task { await viewModel.toggleStarredOnly() } }) {
                            Image(systemName: viewModel.showOnlyStarred ? "star.fill" : "star")
                                .font(.system(size: 16))
                                .foregroundColor(viewModel.showOnlyStarred ? .orange : .gray)
                        }
                    }
                    
                    // 媒体类型过滤
                    HStack(spacing: 8) {
                        ForEach(["全部", "图片", "视频"], id: \.self) { type in
                            Button(action: {
                                Task {
                                    let typeValue: String? = type == "全部" ? nil : (type == "图片" ? "image" : "video")
                                    await viewModel.changeMediaType(typeValue)
                                }
                            }) {
                                Text(type)
                                    .font(.caption)
                                    .padding(.horizontal, 12)
                                    .padding(.vertical, 6)
                                    .background(
                                        (type == "全部" && viewModel.selectedMediaType == nil) ||
                                        (type == "图片" && viewModel.selectedMediaType == "image") ||
                                        (type == "视频" && viewModel.selectedMediaType == "video")
                                        ? Color.blue : Color.gray.opacity(0.2)
                                    )
                                    .foregroundColor(
                                        (type == "全部" && viewModel.selectedMediaType == nil) ||
                                        (type == "图片" && viewModel.selectedMediaType == "image") ||
                                        (type == "视频" && viewModel.selectedMediaType == "video")
                                        ? .white : .secondary
                                    )
                                    .cornerRadius(4)
                            }
                        }
                        Spacer()
                    }
                }
                .padding()
                .background(Color(NSColor.controlBackgroundColor))
                
                // 媒体网格
                if viewModel.isLoading {
                    VStack {
                        Spacer()
                        ProgressView()
                        Spacer()
                    }
                } else if viewModel.media.isEmpty {
                    VStack {
                        Spacer()
                        Image(systemName: "photo.on.rectangle")
                            .font(.system(size: 48))
                            .foregroundColor(.gray)
                        Text("暂无媒体")
                            .foregroundColor(.secondary)
                        Spacer()
                    }
                } else {
                    ScrollView {
                        LazyVGrid(columns: columns, spacing: 8) {
                            ForEach(viewModel.media) { mediaItem in
                                MediaGridItem(media: mediaItem, viewModel: viewModel)
                                    .onTapGesture {
                                        selectedMedia = mediaItem
                                        showImageDetail = true
                                    }
                            }
                            
                            // 加载更多
                            if viewModel.hasMore {
                                VStack {
                                    if viewModel.isLoadingMore {
                                        ProgressView()
                                    } else {
                                        Text("加载更多")
                                            .font(.caption)
                                            .foregroundColor(.secondary)
                                    }
                                }
                                .frame(height: 100)
                                .gridCellUnsizedAxes(.horizontal)
                                .onAppear {
                                    Task {
                                        await viewModel.loadMore()
                                    }
                                }
                            }
                        }
                        .padding(8)
                    }
                }
                
                Spacer()
            }
            
            // 错误提示
            if let error = viewModel.errorMessage {
                VStack {
                    HStack {
                        Text(error)
                            .font(.caption)
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
        .sheet(isPresented: $showImageDetail) {
            if let selected = selectedMedia {
                MediaDetailView(media: selected, viewModel: viewModel)
            }
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

// MARK: - Media Grid Item

struct MediaGridItem: View {
    let media: Media
    let viewModel: MediaLibraryViewModel
    @State private var isHovering = false
    
    var body: some View {
        ZStack(alignment: .topTrailing) {
            // 缩略图
            VStack {
                if let mimeType = media.mimeType, mimeType.contains("image") {
                    AsyncImage(url: URL(string: media.thumbUrl)) { phase in
                        switch phase {
                        case .empty:
                            ProgressView()
                        case .success(let image):
                            image
                                .resizable()
                                .scaledToFill()
                        case .failure:
                            Image(systemName: "photo")
                                .foregroundColor(.gray)
                        @unknown default:
                            EmptyView()
                        }
                    }
                } else if let mimeType = media.mimeType, mimeType.contains("video") {
                    ZStack {
                        AsyncImage(url: URL(string: media.thumbUrl)) { phase in
                            switch phase {
                            case .empty:
                                ProgressView()
                            case .success(let image):
                                image
                                    .resizable()
                                    .scaledToFill()
                            case .failure:
                                Rectangle()
                                    .foregroundColor(.gray)
                            @unknown default:
                                EmptyView()
                            }
                        }
                        
                        Image(systemName: "play.circle.fill")
                            .font(.system(size: 24))
                            .foregroundColor(.white)
                    }
                } else {
                    VStack {
                        Image(systemName: "doc.text")
                            .font(.system(size: 24))
                            .foregroundColor(.gray)
                    }
                    .frame(maxWidth: .infinity, maxHeight: .infinity)
                    .background(Color.gray.opacity(0.2))
                }
            }
            .frame(height: 150)
            .clipped()
            .cornerRadius(4)
            
            // 收藏按钮
            Button(action: {
                Task {
                    await viewModel.toggleMediaStarred(id: media.id)
                }
            }) {
                Image(systemName: media.starred ? "star.fill" : "star")
                    .font(.system(size: 12))
                    .foregroundColor(media.starred ? .orange : .white)
                    .padding(6)
                    .background(Color.black.opacity(0.3))
                    .clipShape(Circle())
            }
            .padding(6)
        }
    }
}

// MARK: - Media Detail View

struct MediaDetailView: View {
    let media: Media
    let viewModel: MediaLibraryViewModel
    @Environment(\.dismiss) var dismiss
    @State private var isHovering = false
    
    var body: some View {
        NavigationView {
            VStack(spacing: 0) {
                // 媒体预览
                VStack {
                    if let mimeType = media.mimeType, mimeType.contains("image") {
                        AsyncImage(url: URL(string: media.fileUrl)) { phase in
                            switch phase {
                            case .empty:
                                ProgressView()
                            case .success(let image):
                                image
                                    .resizable()
                                    .scaledToFit()
                            case .failure:
                                Image(systemName: "photo")
                                    .foregroundColor(.gray)
                            @unknown default:
                                EmptyView()
                            }
                        }
                    } else if let mimeType = media.mimeType, mimeType.contains("video") {
                        ZStack {
                            AsyncImage(url: URL(string: media.thumbUrl)) { phase in
                                switch phase {
                                case .empty:
                                    ProgressView()
                                case .success(let image):
                                    image
                                        .resizable()
                                        .scaledToFit()
                                case .failure:
                                    Rectangle()
                                        .foregroundColor(.gray)
                                @unknown default:
                                    EmptyView()
                                }
                            }
                            
                            Image(systemName: "play.circle.fill")
                                .font(.system(size: 48))
                                .foregroundColor(.white)
                        }
                    } else {
                        VStack {
                            Image(systemName: "doc.text")
                                .font(.system(size: 48))
                                .foregroundColor(.gray)
                        }
                        .frame(maxWidth: .infinity)
                        .frame(height: 300)
                        .background(Color.gray.opacity(0.1))
                    }
                }
                .frame(maxHeight: 400)
                
                ScrollView {
                    VStack(alignment: .leading, spacing: 12) {
                        // 基本信息
                        Group {
                            HStack {
                                Text("文件名")
                                    .font(.caption)
                                    .foregroundColor(.secondary)
                                Spacer()
                                Text(media.filePath.components(separatedBy: "/").last ?? "未知")
                                    .font(.caption)
                                    .lineLimit(1)
                            }
                            
                            if let fileSize = media.fileSize {
                                HStack {
                                    Text("文件大小")
                                        .font(.caption)
                                        .foregroundColor(.secondary)
                                    Spacer()
                                    Text(formatFileSize(fileSize))
                                        .font(.caption)
                                }
                            }
                            
                            if let mimeType = media.mimeType {
                                HStack {
                                    Text("类型")
                                        .font(.caption)
                                        .foregroundColor(.secondary)
                                    Spacer()
                                    Text(mimeType)
                                        .font(.caption)
                                }
                            }
                        }
                        
                        Divider()
                        
                        // 尺寸信息
                        if let width = media.width, let height = media.height {
                            Group {
                                HStack {
                                    Text("尺寸")
                                        .font(.caption)
                                        .foregroundColor(.secondary)
                                    Spacer()
                                    Text("\(width) × \(height)")
                                        .font(.caption)
                                }
                            }
                        }
                        
                        if let duration = media.durationMs {
                            HStack {
                                Text("时长")
                                    .font(.caption)
                                    .foregroundColor(.secondary)
                                Spacer()
                                Text(formatDuration(duration))
                                    .font(.caption)
                            }
                        }
                        
                        if media.rating > 0 {
                            HStack {
                                Text("评分")
                                    .font(.caption)
                                    .foregroundColor(.secondary)
                                Spacer()
                                HStack(spacing: 2) {
                                    ForEach(0..<5, id: \.self) { index in
                                        Image(systemName: index < media.rating ? "star.fill" : "star")
                                            .font(.system(size: 10))
                                            .foregroundColor(.orange)
                                    }
                                }
                            }
                        }
                        
                        Divider()
                        
                        // 时间信息
                        Group {
                            HStack {
                                Text("创建时间")
                                    .font(.caption)
                                    .foregroundColor(.secondary)
                                Spacer()
                                Text(formatDate(media.createdAt))
                                    .font(.caption)
                            }
                        }
                        
                        // 标签
                        if !media.tags.isEmpty {
                            VStack(alignment: .leading, spacing: 8) {
                                Text("标签")
                                    .font(.caption)
                                    .foregroundColor(.secondary)
                                
                                FlowLayout {
                                    ForEach(media.tags) { tag in
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
                        }
                    }
                    .padding()
                }
            }
            .navigationTitle("媒体详情")
            .toolbar {
                ToolbarItem(placement: .automatic) {
                    Button(action: {
                        Task {
                            await viewModel.toggleMediaStarred(id: media.id)
                        }
                    }) {
                        Image(systemName: media.starred ? "star.fill" : "star")
                            .foregroundColor(media.starred ? .orange : .gray)
                    }
                }
            }
        }
    }
    
    private func formatFileSize(_ bytes: Int) -> String {
        let formatter = ByteCountFormatter()
        formatter.allowedUnits = [.useKB, .useMB, .useGB]
        formatter.countStyle = .file
        return formatter.string(fromByteCount: Int64(bytes))
    }
    
    private func formatDuration(_ ms: Int) -> String {
        let seconds = ms / 1000
        let minutes = seconds / 60
        let hours = minutes / 60
        
        if hours > 0 {
            return String(format: "%d:%02d:%02d", hours, minutes % 60, seconds % 60)
        } else {
            return String(format: "%d:%02d", minutes, seconds % 60)
        }
    }
    
    private func formatDate(_ dateString: String) -> String {
        let formatter = ISO8601DateFormatter()
        if let date = formatter.date(from: dateString) {
            let dateFormatter = DateFormatter()
            dateFormatter.locale = Locale(identifier: "zh_CN")
            dateFormatter.dateFormat = "yyyy年MM月dd日 HH:mm"
            return dateFormatter.string(from: date)
        }
        return dateString
    }
}

// MARK: - Flow Layout (用于标签排列)

struct FlowLayout: Layout {
    func sizeThatFits(proposal: ProposedViewSize, subviews: Subviews, cache: inout ()) -> CGSize {
        let result = FlowResult(
            in: proposal.replacingUnspecifiedDimensions(by: CGSize(width: 300, height: 300)),
            subviews: subviews
        )
        return result.size
    }
    
    func placeSubviews(in bounds: CGRect, proposal: ProposedViewSize, subviews: Subviews, cache: inout ()) {
        let result = FlowResult(
            in: proposal.replacingUnspecifiedDimensions(by: bounds.size),
            subviews: subviews
        )
        
        for (index, offset) in result.offsets.enumerated() {
            subviews[index].place(at: CGPoint(x: bounds.minX + offset.x, y: bounds.minY + offset.y), proposal: ProposedViewSize(result.sizes[index]))
        }
    }
    
    struct FlowResult {
        var size = CGSize.zero
        var offsets: [CGPoint] = []
        var sizes: [CGSize] = []
        
        init(in bounds: CGSize, subviews: Subviews) {
            var x: CGFloat = 0
            var y: CGFloat = 0
            var maxY: CGFloat = 0
            
            for subview in subviews {
                let size = subview.sizeThatFits(.unspecified)
                
                if x + size.width > bounds.width {
                    x = 0
                    y = maxY + 8
                }
                
                offsets.append(CGPoint(x: x, y: y))
                sizes.append(size)
                
                x += size.width + 8
                maxY = max(maxY, y + size.height)
            }
            
            self.size = CGSize(width: bounds.width, height: maxY)
        }
    }
}

#Preview {
    MediaLibraryView()
}

