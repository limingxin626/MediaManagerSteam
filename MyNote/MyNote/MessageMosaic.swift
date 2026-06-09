//
//  MessageMosaic.swift
//  MyNote
//
//  Telegram 风格 Mosaic 布局算法 —— 从 vue 端 `vue/src/utils/mosaic.ts` 移植。
//  根据图片宽高比动态计算最优行分配和尺寸权重,避免单 / 双图场景下图片
//  占满整张卡而显得过宽。
//
//  算法要点:
//    1. 每张图 ratio 夹紧到 [0.667, 1.7](超长图 / 超竖图都不参与 layout 决策)
//    2. 1 张 → 单行 rows,heightWeight = W / ratio
//    3. 2 张 → 同为超宽 (ratio > 1.6 且差 < 0.2) 才上下排,否则按 ratio 加权一行内并排
//    4. 3+ 张 → 贪心搜索 1~4 行的 partition,最小化 cell 面积方差,避开
//       太瘦的 cell (lineHeight < W*0.28 / itemArea < W² * 0.04)
//    5. (早期版本的「3 张 L 型」特殊分支已删除 — 3 张图也走贪心,与 4+ 行为一致)
//
//  所有 heightWeight / widthWeight 都是在「虚拟容器宽度 W = 400」下的相对值;
//  SwiftUI 端用 GeometryReader 拿实际容器宽度,按比例换算成实际像素。
//

import Foundation

// MARK: - 类型

enum MosaicType {
    /// 多行(rows 内单行 HStack,rows 之间 VStack)
    case rows
}

struct MosaicItem {
    let index: Int
    let widthWeight: Double
}

struct MosaicRow {
    let items: [MosaicItem]
    let heightWeight: Double
}

struct MosaicLayout {
    let type: MosaicType
    let rows: [MosaicRow]
    let leftColumnWidth: Double
    let leftColumnIndex: Int
}

// MARK: - 入口

/// 给一组图片宽高比,算出最优 mosaic 布局。
/// - Parameters:
///   - ratios: 每张图的 width/height,缺失 / 非法时调用方已填默认值 1.5
///   - containerWidth: 虚拟容器宽度(对齐 vue 端 MOSAIC_CONTAINER_WIDTH = 400)
func calculateMosaicLayout(
    ratios: [Double],
    containerWidth: Double = 400
) -> MosaicLayout {
    if ratios.isEmpty {
        return MosaicLayout(type: .rows, rows: [], leftColumnWidth: 0, leftColumnIndex: 0)
    }
    if ratios.count < 2 {
        let r = ratios[0]
        return MosaicLayout(
            type: .rows,
            rows: [MosaicRow(
                items: [MosaicItem(index: 0, widthWeight: 1)],
                heightWeight: containerWidth / r
            )],
            leftColumnWidth: 0,
            leftColumnIndex: 0
        )
    }

    let clamped = ratios.map { min(1.7, max(0.667, $0)) }
    let count = ratios.count

    if count == 2 {
        return layoutTwo(clamped: clamped, original: ratios, w: containerWidth)
    }
    return layoutOptimized(ratios: clamped, containerWidth: containerWidth)
}

// MARK: - 分类

private enum RatioClass { case wide, quasi, narrow }

private func classify(_ ratio: Double) -> RatioClass {
    if ratio > 1.2 { return .wide }
    if ratio < 0.8 { return .narrow }
    return .quasi
}

// MARK: - 2 张布局

private func layoutTwo(clamped: [Double], original: [Double], w: Double) -> MosaicLayout {
    let c0 = classify(original[0])
    let c1 = classify(original[1])

    // 电脑屏宽:只有两张都超宽且比例相近时才上下排
    if c0 == .wide && c1 == .wide
        && original[0] > 1.6 && original[1] > 1.6
        && abs(original[0] - original[1]) < 0.2 {
        return MosaicLayout(
            type: .rows,
            rows: [
                MosaicRow(
                    items: [MosaicItem(index: 0, widthWeight: 1)],
                    heightWeight: w / clamped[0]
                ),
                MosaicRow(
                    items: [MosaicItem(index: 1, widthWeight: 1)],
                    heightWeight: w / clamped[1]
                ),
            ],
            leftColumnWidth: 0,
            leftColumnIndex: 0
        )
    }

    // 否则一行内按 ratio 加权
    let total = clamped[0] + clamped[1]
    return MosaicLayout(
        type: .rows,
        rows: [
            MosaicRow(
                items: [
                    MosaicItem(index: 0, widthWeight: clamped[0] / total),
                    MosaicItem(index: 1, widthWeight: clamped[1] / total),
                ],
                heightWeight: w / total
            ),
        ],
        leftColumnWidth: 0,
        leftColumnIndex: 0
    )
}

// MARK: - 3+ 张布局:贪心搜索 partition

private func layoutOptimized(ratios: [Double], containerWidth: Double) -> MosaicLayout {
    let count = ratios.count
    let maxLines = min(4, count)
    let maxPerLine = 5

    var bestVariance = Double.infinity
    var bestPartition: [Int]? = nil

    let minLineHeight = containerWidth * 0.28
    let minItemArea = containerWidth * containerWidth * 0.04

    func search(_ remaining: Int, _ lines: Int, _ partition: inout [Int]) {
        if lines == 0 {
            if remaining != 0 { return }
            var areas: [Double] = []
            var idx = 0
            for lineCount in partition {
                var lineRatioSum = 0.0
                for i in idx..<(idx + lineCount) {
                    lineRatioSum += ratios[i]
                }
                let lineHeight = containerWidth / lineRatioSum
                if lineHeight < minLineHeight { return }
                for i in idx..<(idx + lineCount) {
                    let itemWidth = containerWidth * ratios[i] / lineRatioSum
                    let area = itemWidth * lineHeight
                    if area < minItemArea { return }
                    areas.append(area)
                }
                idx += lineCount
            }
            let mean = areas.reduce(0, +) / Double(areas.count)
            let variance = areas.reduce(0) { $0 + ($1 - mean) * ($1 - mean) } / Double(areas.count)
            if variance < bestVariance {
                bestVariance = variance
                bestPartition = partition
            }
            return
        }
        let maxThisLine = min(remaining - lines + 1, maxPerLine)
        for n in 1...maxThisLine {
            partition.append(n)
            search(remaining - n, lines - 1, &partition)
            partition.removeLast()
        }
    }

    for numLines in 1...maxLines {
        var partition: [Int] = []
        search(count, numLines, &partition)
    }

    let partition: [Int]
    if let best = bestPartition {
        partition = best
    } else {
        // fallback:均分到 ceil(count / 4) 行
        let lines = Int((Double(count) / Double(maxPerLine)).rounded(.up))
        let base = count / lines
        let extra = count - base * lines
        partition = (0..<lines).map { i in base + (i < extra ? 1 : 0) }
    }

    var rows: [MosaicRow] = []
    var idx = 0
    for lineCount in partition {
        var lineRatioSum = 0.0
        for i in idx..<(idx + lineCount) {
            lineRatioSum += ratios[i]
        }
        let lineHeight = containerWidth / lineRatioSum
        var items: [MosaicItem] = []
        for i in idx..<(idx + lineCount) {
            items.append(MosaicItem(index: i, widthWeight: ratios[i] / lineRatioSum))
        }
        rows.append(MosaicRow(items: items, heightWeight: lineHeight))
        idx += lineCount
    }

    return MosaicLayout(type: .rows, rows: rows, leftColumnWidth: 0, leftColumnIndex: 0)
}
