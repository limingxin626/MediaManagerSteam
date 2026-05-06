/**
 * Telegram 风格 Mosaic 布局算法（从 Android MosaicLayout.kt 移植）
 * 根据图片宽高比动态计算最优行分配和尺寸权重
 */

export type MosaicType = 'rows' | 'left_column'

export interface MosaicItem {
  index: number
  widthWeight: number
}

export interface MosaicRow {
  items: MosaicItem[]
  heightWeight: number
}

export interface MosaicLayout {
  type: MosaicType
  rows: MosaicRow[]
  leftColumnWidth: number
  leftColumnIndex: number
}

function classify(ratio: number): 'w' | 'n' | 'q' {
  if (ratio > 1.2) return 'w'
  if (ratio < 0.8) return 'n'
  return 'q'
}

function layoutTwo(clamped: number[], original: number[], w: number): MosaicLayout {
  const c0 = classify(original[0])
  const c1 = classify(original[1])

  // Vue: 电脑屏幕宽，只有两张都非常宽且比例相近时才上下排列
  if (c0 === 'w' && c1 === 'w' && original[0] > 1.6 && original[1] > 1.6 && Math.abs(original[0] - original[1]) < 0.2) {
    return {
      type: 'rows',
      rows: [
        { items: [{ index: 0, widthWeight: 1 }], heightWeight: w / clamped[0] },
        { items: [{ index: 1, widthWeight: 1 }], heightWeight: w / clamped[1] },
      ],
      leftColumnWidth: 0,
      leftColumnIndex: 0,
    }
  }

  const total = clamped[0] + clamped[1]
  return {
    type: 'rows',
    rows: [
      {
        items: [
          { index: 0, widthWeight: clamped[0] / total },
          { index: 1, widthWeight: clamped[1] / total },
        ],
        heightWeight: w / total,
      },
    ],
    leftColumnWidth: 0,
    leftColumnIndex: 0,
  }
}

function layoutThree(clamped: number[], original: number[], w: number): MosaicLayout {
  if (classify(original[0]) === 'w') {
    const bottomTotal = clamped[1] + clamped[2]
    return {
      type: 'rows',
      rows: [
        { items: [{ index: 0, widthWeight: 1 }], heightWeight: w / clamped[0] },
        {
          items: [
            { index: 1, widthWeight: clamped[1] / bottomTotal },
            { index: 2, widthWeight: clamped[2] / bottomTotal },
          ],
          heightWeight: w / bottomTotal,
        },
      ],
      leftColumnWidth: 0,
      leftColumnIndex: 0,
    }
  }

  // L 型布局
  const rightAvg = (clamped[1] + clamped[2]) / 2
  const leftW = clamped[0] / (clamped[0] + rightAvg)
  const h1 = 1 / clamped[1]
  const h2 = 1 / clamped[2]
  return {
    type: 'left_column',
    leftColumnWidth: leftW,
    leftColumnIndex: 0,
    rows: [
      { items: [{ index: 1, widthWeight: 1 }], heightWeight: h1 },
      { items: [{ index: 2, widthWeight: 1 }], heightWeight: h2 },
    ],
  }
}

function layoutOptimized(ratios: number[], containerWidth: number): MosaicLayout {
  const count = ratios.length
  const maxLines = Math.min(4, count)
  const maxPerLine = 4

  let bestVariance = Infinity
  let bestPartition: number[] | null = null

  const minLineHeight = containerWidth * 0.28
  const minItemArea = containerWidth * containerWidth * 0.04

  function search(remaining: number, lines: number, partition: number[]) {
    if (lines === 0) {
      if (remaining !== 0) return
      const areas: number[] = []
      let idx = 0
      for (const lineCount of partition) {
        let lineRatioSum = 0
        for (let i = idx; i < idx + lineCount; i++) lineRatioSum += ratios[i]
        const lineHeight = containerWidth / lineRatioSum
        if (lineHeight < minLineHeight) return
        for (let i = idx; i < idx + lineCount; i++) {
          const itemWidth = containerWidth * ratios[i] / lineRatioSum
          const area = itemWidth * lineHeight
          if (area < minItemArea) return
          areas.push(area)
        }
        idx += lineCount
      }
      const mean = areas.reduce((a, b) => a + b, 0) / areas.length
      const variance = areas.reduce((a, b) => a + (b - mean) ** 2, 0) / areas.length
      if (variance < bestVariance) {
        bestVariance = variance
        bestPartition = [...partition]
      }
      return
    }
    const maxThisLine = Math.min(remaining - lines + 1, maxPerLine)
    for (let n = 1; n <= maxThisLine; n++) {
      partition.push(n)
      search(remaining - n, lines - 1, partition)
      partition.pop()
    }
  }

  for (let numLines = 1; numLines <= maxLines; numLines++) {
    search(count, numLines, [])
  }

  let partition: number[]
  if (bestPartition) {
    partition = bestPartition
  } else {
    const lines = Math.ceil(count / maxPerLine)
    const base = Math.floor(count / lines)
    const extra = count - base * lines
    partition = Array.from({ length: lines }, (_, i) => base + (i < extra ? 1 : 0))
  }
  const rows: MosaicRow[] = []
  let idx = 0
  for (const lineCount of partition) {
    let lineRatioSum = 0
    for (let i = idx; i < idx + lineCount; i++) lineRatioSum += ratios[i]
    const lineHeight = containerWidth / lineRatioSum
    const items: MosaicItem[] = []
    for (let i = idx; i < idx + lineCount; i++) {
      items.push({ index: i, widthWeight: ratios[i] / lineRatioSum })
    }
    rows.push({ items, heightWeight: lineHeight })
    idx += lineCount
  }

  return { type: 'rows', rows, leftColumnWidth: 0, leftColumnIndex: 0 }
}

export function calculateMosaicLayout(ratios: number[], containerWidth = 400): MosaicLayout {
  if (ratios.length < 2) {
    return {
      type: 'rows',
      rows: [{ items: [{ index: 0, widthWeight: 1 }], heightWeight: containerWidth / (ratios[0] || 1.5) }],
      leftColumnWidth: 0,
      leftColumnIndex: 0,
    }
  }

  const clamped = ratios.map(r => Math.min(1.7, Math.max(0.667, r)))
  const count = ratios.length

  if (count === 2) return layoutTwo(clamped, ratios, containerWidth)
  if (count === 3) return layoutThree(clamped, ratios, containerWidth)
  return layoutOptimized(clamped, containerWidth)
}
