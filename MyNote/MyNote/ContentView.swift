//
//  ContentView.swift
//  MyNote
//
//  Created by 西门吹雪 on 2026/6/4.
//

import SwiftUI

struct ContentView: View {
    var body: some View {
        TabView {
            FeedView()
                .tabItem {
                    Label("消息", systemImage: "list.bullet")
                }
            
            MediaLibraryView()
                .tabItem {
                    Label("媒体库", systemImage: "photo.on.rectangle")
                }
        }
    }
}

#Preview {
    ContentView()
}
