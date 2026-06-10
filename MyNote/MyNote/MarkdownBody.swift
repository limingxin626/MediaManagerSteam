//
//  MarkdownBody.swift
//  MyNote
//
//  消息正文 markdown 渲染 —— 基于 swift-markdown-ui 的 `Markdown` view
//  做一层薄封装,统一字体 / 间距 / 主题,便于消息域 (MessageCard) 共用。
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
        Markdown(Self.softBreakToHardBreak(text))
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

    // 把段落内的单个换行(soft break)转成 CommonMark 硬换行(行尾两空格 + \n),
    // 对齐 vue 端 `marked` 的 `breaks: true` 行为。否则 swift-markdown-ui
    // 按 CommonMark 严格语义把单换行当作空格,导致用户视觉上分两行的内容被拼到一起。
    //
    // 围栏代码块(``` 或 ~~~)与缩进代码块原样保留,避免破坏代码格式。
    static func softBreakToHardBreak(_ raw: String) -> String {
        let normalized = raw.replacingOccurrences(of: "\r\n", with: "\n")
                            .replacingOccurrences(of: "\r", with: "\n")
        var out: [String] = []
        var inFence = false
        var fenceMarker: Character = "`"
        let lines = normalized.split(separator: "\n", omittingEmptySubsequences: false)
        for (idx, sub) in lines.enumerated() {
            let line = String(sub)
            let trimmed = line.trimmingCharacters(in: .whitespaces)
            if !inFence, trimmed.hasPrefix("```") || trimmed.hasPrefix("~~~") {
                inFence = true
                fenceMarker = trimmed.first!
                out.append(line)
                continue
            }
            if inFence {
                out.append(line)
                if trimmed.hasPrefix(String(repeating: fenceMarker, count: 3)) {
                    inFence = false
                }
                continue
            }
            let isLast = idx == lines.count - 1
            let nextIsBlank = !isLast && lines[idx + 1].trimmingCharacters(in: .whitespaces).isEmpty
            let alreadyHardBreak = line.hasSuffix("  ") || line.hasSuffix("\\")
            if isLast || nextIsBlank || trimmed.isEmpty || alreadyHardBreak {
                out.append(line)
            } else {
                out.append(line + "  ")
            }
        }
        return out.joined(separator: "\n")
    }
}
