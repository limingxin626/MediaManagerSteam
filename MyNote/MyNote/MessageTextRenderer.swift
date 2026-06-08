//
//  MessageTextRenderer.swift
//  MyNote
//
//  消息正文渲染 —— inline markdown(粗体/斜体/行内代码/链接/删除线)
//  + 裸 URL 自动检测,返回可直接喂给 `Text` 的 `AttributedString`。
//
//  覆盖范围:**仅 inline markdown**(MessageCard / MessageDetailPane 共用)。
//  与 vue 端 `marked` 全功能渲染**不一致**:
//    - 不支持块级语法(`#` 标题、`-`/`*` 列表、`>` 引用、围栏代码块)
//      → 会原样以文本出现。
//    - 一行一段:换行被 SwiftUI Text 按视图宽度自动 wrap;markdown 的
//      段落空行规则不另外处理。
//
//  保留逻辑:
//    - 文本中的裸 URL(没有写成 `[label](url)` 的)仍会自动变成可点链接,
//      不依赖 markdown 解析(NSDataDetector 兜底)。
//    - markdown 解析失败时整体降级为纯文本 + 裸 URL 检测,不会掉内容。
//

import Foundation
import SwiftUI

enum MessageTextRenderer {

    /// 把 message text 解析成 `AttributedString`:
    ///   1. 用 `AttributedString(markdown:options:)` 解析 inline markdown
    ///      (`interpretedSyntax = .inlineOnlyPreservingWhitespace` 保留换行)
    ///   2. 对解析后字符串里仍以"裸文本"形式存在的 URL 走 `NSDataDetector` 上色 + 挂 link
    ///   3. markdown 解析失败时退化成纯文本 + 裸 URL 检测
    static func render(_ text: String) -> AttributedString {
        let base = parseInlineMarkdown(text) ?? AttributedString(text)
        return applyBareURLDetection(to: base)
    }

    // MARK: - 私有

    /// SwiftUI 原生 markdown 解析。`.inlineOnlyPreservingWhitespace` 选项很关键:
    ///   - inlineOnly:不识别块级语法(标题/列表/引用等),那些字符按字面保留
    ///   - preservingWhitespace:换行 / 多余空白不被压缩,长文本里的换行会被保留
    private static func parseInlineMarkdown(_ text: String) -> AttributedString? {
        let options = AttributedString.MarkdownParsingOptions(
            allowsExtendedAttributes: false,
            interpretedSyntax: .inlineOnlyPreservingWhitespace,
            failurePolicy: .returnPartiallyParsedIfPossible
        )
        return try? AttributedString(markdown: text, options: options)
    }

    /// 对 `AttributedString` 里"还没被 markdown 解析成 link"的裸 URL 子串
    /// 做 NSDataDetector 检测,挂上 `.link` + 上色。已经有 link 属性的 run
    /// 跳过(避免覆盖 `[label](url)` 形式的 markdown 链接)。
    private static func applyBareURLDetection(to attr: AttributedString) -> AttributedString {
        var result = attr
        let plain = String(result.characters)
        guard !plain.isEmpty,
              let detector = try? NSDataDetector(types: NSTextCheckingResult.CheckingType.link.rawValue)
        else { return result }

        let range = NSRange(location: 0, length: (plain as NSString).length)
        let matches = detector.matches(in: plain, options: [], range: range)
        guard !matches.isEmpty else { return result }

        for m in matches {
            guard let url = m.url,
                  let swiftRange = Range(m.range, in: plain),
                  let attrRange = Range(swiftRange, in: result)
            else { continue }
            // 已经是 markdown link 的 run 不覆盖
            if result[attrRange].link != nil { continue }
            result[attrRange].link = url
            result[attrRange].foregroundColor = .accentColor
        }
        return result
    }
}
