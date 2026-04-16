package com.example.myapplication.ui.components

import kotlin.math.abs


/**
 * Telegram 风格 Mosaic 布局算法
 * 根据图片宽高比动态计算最优行分配和尺寸权重
 *
 * heightWeight 含义：
 * - ROWS 类型：每行的像素高度
 * - LEFT_COLUMN 类型：右列每行的相对高度权重（均等）
 */

enum class MosaicType {
    ROWS,
    LEFT_COLUMN,
}

data class MosaicLayout(
    val type: MosaicType,
    val rows: List<MosaicRow>,
    val leftColumnWidth: Float = 0f,
    val leftColumnIndex: Int = 0,
)

data class MosaicRow(
    val items: List<MosaicItem>,
    val heightWeight: Float
)

data class MosaicItem(
    val index: Int,
    val widthWeight: Float
)

fun calculateMosaicLayout(ratios: List<Float>, containerWidth: Float = 400f): MosaicLayout {
    require(ratios.size >= 2) { "Mosaic layout requires at least 2 images" }

    val count = ratios.size
    val clamped = ratios.map { it.coerceIn(0.667f, 1.7f) }

    return when (count) {
        2 -> layoutTwo(clamped, ratios, containerWidth)
        3 -> layoutThree(clamped, ratios, containerWidth)
        else -> layoutOptimized(clamped, containerWidth)
    }
}

private fun classify(ratio: Float): Char = when {
    ratio > 1.2f -> 'w'
    ratio < 0.8f -> 'n'
    else -> 'q'
}

private fun layoutTwo(clamped: List<Float>, original: List<Float>, w: Float): MosaicLayout {
    val c0 = classify(original[0])
    val c1 = classify(original[1])

    // 两张都是宽图且比例相近 → 上下排列
    if (c0 == 'w' && c1 == 'w' && abs(original[0] - original[1]) < 0.2f) {
        return MosaicLayout(
            type = MosaicType.ROWS,
            rows = listOf(
                MosaicRow(listOf(MosaicItem(0, 1f)), w / clamped[0]),
                MosaicRow(listOf(MosaicItem(1, 1f)), w / clamped[1])
            )
        )
    }

    // 左右并排：行高 = containerWidth / (ratio0 + ratio1)
    val total = clamped[0] + clamped[1]
    return MosaicLayout(
        type = MosaicType.ROWS,
        rows = listOf(
            MosaicRow(
                listOf(
                    MosaicItem(0, clamped[0] / total),
                    MosaicItem(1, clamped[1] / total)
                ),
                w / total
            )
        )
    )
}

private fun layoutThree(clamped: List<Float>, original: List<Float>, w: Float): MosaicLayout {
    if (classify(original[0]) == 'w') {
        // 首图宽 → 上方全宽 + 下方两列
        val bottomTotal = clamped[1] + clamped[2]
        return MosaicLayout(
            type = MosaicType.ROWS,
            rows = listOf(
                MosaicRow(listOf(MosaicItem(0, 1f)), w / clamped[0]),
                MosaicRow(
                    listOf(
                        MosaicItem(1, clamped[1] / bottomTotal),
                        MosaicItem(2, clamped[2] / bottomTotal)
                    ),
                    w / bottomTotal
                )
            )
        )
    }

    // L 型：左列图0，右列图1+图2
    // 右列行高按 1/ratio 分配（窄图高、宽图矮）
    val rightAvg = (clamped[1] + clamped[2]) / 2f
    val leftW = clamped[0] / (clamped[0] + rightAvg)
    val h1 = 1f / clamped[1]
    val h2 = 1f / clamped[2]
    return MosaicLayout(
        type = MosaicType.LEFT_COLUMN,
        leftColumnWidth = leftW,
        leftColumnIndex = 0,
        rows = listOf(
            MosaicRow(listOf(MosaicItem(1, 1f)), h1),
            MosaicRow(listOf(MosaicItem(2, 1f)), h2)
        )
    )
}

private fun layoutFour(clamped: List<Float>, original: List<Float>, w: Float): MosaicLayout {
    if (classify(original[0]) == 'w') {
        // 首图宽 → 上方全宽 + 下方三列
        val bottomRatios = clamped.subList(1, 4)
        val bottomTotal = bottomRatios.sum()
        return MosaicLayout(
            type = MosaicType.ROWS,
            rows = listOf(
                MosaicRow(listOf(MosaicItem(0, 1f)), w / clamped[0]),
                MosaicRow(
                    bottomRatios.mapIndexed { i, r -> MosaicItem(i + 1, r / bottomTotal) },
                    w / bottomTotal
                )
            )
        )
    }

    // 左列图0，右列图1+图2+图3
    // 右列行高按 1/ratio 分配（窄图高、宽图矮）
    val rightAvg = (clamped[1] + clamped[2] + clamped[3]) / 3f
    val leftW = clamped[0] / (clamped[0] + rightAvg)
    val h1 = 1f / clamped[1]
    val h2 = 1f / clamped[2]
    val h3 = 1f / clamped[3]
    return MosaicLayout(
        type = MosaicType.LEFT_COLUMN,
        leftColumnWidth = leftW,
        leftColumnIndex = 0,
        rows = listOf(
            MosaicRow(listOf(MosaicItem(1, 1f)), h1),
            MosaicRow(listOf(MosaicItem(2, 1f)), h2),
            MosaicRow(listOf(MosaicItem(3, 1f)), h3)
        )
    )
}

/**
 * 4+ 图：遍历所有行分配方案
 * 硬约束：每行最小高度 28%、每张图最小面积阈值
 * 评分：在满足约束的方案中，选面积方差最小的（让各图面积尽量均匀）
 */
private fun layoutOptimized(ratios: List<Float>, containerWidth: Float): MosaicLayout {
    val count = ratios.size
    val maxLines = 4.coerceAtMost(count)
    val maxPerLine = 4.coerceAtMost(count)

    var bestVariance = Float.MAX_VALUE
    var bestPartition: List<Int>? = null

    // 硬约束
    val minLineHeight = containerWidth * 0.28f
    val minItemArea = containerWidth * containerWidth * 0.04f // 每张图至少占容器面积的 4%

    fun search(remaining: Int, lines: Int, partition: MutableList<Int>) {
        if (lines == 0) {
            if (remaining == 0) {
                val areas = mutableListOf<Float>()
                var idx = 0
                for (lineCount in partition) {
                    val lineRatioSum = (idx until idx + lineCount).sumOf { ratios[it].toDouble() }.toFloat()
                    val lineHeight = containerWidth / lineRatioSum
                    if (lineHeight < minLineHeight) return
                    for (i in idx until idx + lineCount) {
                        val itemWidth = containerWidth * ratios[i] / lineRatioSum
                        val area = itemWidth * lineHeight
                        if (area < minItemArea) return
                        areas.add(area)
                    }
                    idx += lineCount
                }
                // 评分：面积方差越小越好
                val mean = areas.average().toFloat()
                val variance = areas.sumOf { ((it - mean) * (it - mean)).toDouble() }.toFloat() / areas.size
                if (variance < bestVariance) {
                    bestVariance = variance
                    bestPartition = partition.toList()
                }
            }
            return
        }
        val maxThisLine = (remaining - lines + 1).coerceAtMost(maxPerLine)
        for (n in 1..maxThisLine) {
            partition.add(n)
            search(remaining - n, lines - 1, partition)
            partition.removeAt(partition.lastIndex)
        }
    }

    for (numLines in 1..maxLines) {
        search(count, numLines, mutableListOf())
    }

    val partition = bestPartition ?: listOf(count)

    val rows = mutableListOf<MosaicRow>()
    var idx = 0
    for (lineCount in partition) {
        val lineRatios = ratios.subList(idx, idx + lineCount)
        val lineRatioSum = lineRatios.sum()
        val lineHeight = containerWidth / lineRatioSum
        rows.add(MosaicRow(
            lineRatios.mapIndexed { i, r -> MosaicItem(idx + i, r / lineRatioSum) },
            lineHeight
        ))
        idx += lineCount
    }

    return MosaicLayout(type = MosaicType.ROWS, rows = rows)
}
