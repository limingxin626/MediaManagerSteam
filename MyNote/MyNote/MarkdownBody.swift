//
//  MarkdownBody.swift
//  MyNote
//
//  消息正文 markdown 渲染 —— 基于 swift-markdown-ui 的 `Markdown` view
//  做一层薄封装,统一字体 / 间距 / 主题,便于 MessageCard / MessageDetailPane 共用。
//
//  支持范围(GitHub Flavored Markdown 全集):
//    - 标题 H1-H6
//    - 有序 / 无序 / 任务列表
//    - 引用块、围栏代码块、行内代码
//    - 加粗、斜体、删除线、链接、图片
//    - 表格(macOS 13+,我们 deployment target 26.4 满足)
//    - 分隔线
//
//  与 vue 端 `marked` 渲染基本对齐(都遵循 CommonMark + GFM)。
//
//  接入 SPM:见 `MAC_TODO.md` 1.6 节。
//

import SwiftUI
import MarkdownUI

struct MarkdownBody: View {
    let text: String

    var body: some View {
        Markdown(text)
            // 基础正文字号对齐原 inline 渲染(14pt),与 MessageCard 其他文本一致
            .markdownTextStyle(\.text) {
                FontSize(14)
            }
            // 行内代码:等宽 + 浅灰底,与 vue 端 prose 类近似
            .markdownTextStyle(\.code) {
                FontFamilyVariant(.monospaced)
                FontSize(.em(0.9))
                BackgroundColor(.secondary.opacity(0.15))
            }
            // 链接:沿用 accent color(原 NSDataDetector 高亮一致)
            .markdownTextStyle(\.link) {
                ForegroundColor(.accentColor)
            }
            // 标题分级缩放(default theme 没有显著差异,这里给一份贴合消息卡片密度的)
            .markdownBlockStyle(\.heading1) { configuration in
                configuration.label
                    .markdownTextStyle {
                        FontSize(20)
                        FontWeight(.semibold)
                    }
                    .padding(.top, 4)
                    .padding(.bottom, 2)
            }
            .markdownBlockStyle(\.heading2) { configuration in
                configuration.label
                    .markdownTextStyle {
                        FontSize(17)
                        FontWeight(.semibold)
                    }
                    .padding(.top, 4)
                    .padding(.bottom, 2)
            }
            .markdownBlockStyle(\.heading3) { configuration in
                configuration.label
                    .markdownTextStyle {
                        FontSize(15)
                        FontWeight(.semibold)
                    }
                    .padding(.top, 2)
            }
            // 围栏代码块:浅底 + 圆角 + 内边距,与卡片背景区分开
            .markdownBlockStyle(\.codeBlock) { configuration in
                configuration.label
                    .markdownTextStyle {
                        FontFamilyVariant(.monospaced)
                        FontSize(.em(0.88))
                    }
                    .padding(10)
                    .frame(maxWidth: .infinity, alignment: .leading)
                    .background(Color.secondary.opacity(0.10))
                    .clipShape(RoundedRectangle(cornerRadius: 6))
            }
            // 引用块:左侧粗竖线 + 灰字
            .markdownBlockStyle(\.blockquote) { configuration in
                configuration.label
                    .markdownTextStyle {
                        ForegroundColor(.secondary)
                    }
                    .padding(.leading, 10)
                    .overlay(alignment: .leading) {
                        Rectangle()
                            .fill(Color.secondary.opacity(0.4))
                            .frame(width: 3)
                    }
            }
            .textSelection(.enabled)
    }
}
