//
//  MediaLibraryView.swift
//  MyNote
//
//  媒体库视图 - 网格展示所有媒体(本地 SQLite 数据源)。
//

import SwiftUI

struct MediaLibraryView: View {
    @StateObject private var viewModel = MediaLibraryViewModel()
    @State private var selectedMedia: Media? = nil

    let columns = [
        GridItem(.flexible(), spacing: 8),
        GridItem(.flexible(), spacing: 8),
        GridItem(.flexible(), spacing: 8),
        GridItem(.flexible(), spacing: 8)
    ]

    var body: some View {
        ZStack {
            VStack(spacing: 0) {
                header

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
                    grid
                }

                Spacer(minLength: 0)
            }

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
        .sheet(item: $selectedMedia) { media in
            MediaDetailView(media: media)
        }
        .onAppear {
            Task { await viewModel.loadInitial() }
        }
        .refreshable {
            await viewModel.refresh()
        }
    }

    // MARK: - Header

    private var header: some View {
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
    }

    // MARK: - Grid

    private var grid: some View {
        ScrollView {
            LazyVGrid(columns: columns, spacing: 8) {
                ForEach(viewModel.media) { mediaItem in
                    MediaGridItem(media: mediaItem)
                        .onTapGesture {
                            selectedMedia = mediaItem
                        }
                }

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
                        Task { await viewModel.loadMore() }
                    }
                }
            }
            .padding(8)
        }
    }
}

// MARK: - Grid Item

struct MediaGridItem: View {
    let media: Media

    var body: some View {
        ZStack(alignment: .topTrailing) {
            ZStack {
                LocalThumbView(media: media)

                if let mime = media.mimeType, mime.hasPrefix("video/") {
                    Image(systemName: "play.circle.fill")
                        .font(.system(size: 24))
                        .foregroundColor(.white)
                        .shadow(radius: 2)
                }
            }
            .aspectRatio(1, contentMode: .fit)
            .clipped()
            .cornerRadius(4)
            .contentShape(Rectangle())

            // 第一期只读:星标仅显示状态,不可点击
            if media.starred {
                Image(systemName: "star.fill")
                    .font(.system(size: 12))
                    .foregroundColor(.orange)
                    .padding(6)
                    .background(Color.black.opacity(0.3))
                    .clipShape(Circle())
                    .padding(6)
            }
        }
    }
}

#Preview {
    MediaLibraryView()
}
