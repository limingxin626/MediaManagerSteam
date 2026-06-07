//
//  PreviewTitle.swift
//  MyNote
//
//  @Observable holder for the preview window title — written by MediaDetailView
//  on index change, read by NavigationStack for the window title bar.
//

import SwiftUI

@Observable
final class PreviewTitle {
    static let shared = PreviewTitle()

    var title: String = ""

    private init() {}
}