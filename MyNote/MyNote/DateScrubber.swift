//
//  DateScrubber.swift
//  MyNote
//
//  时间轴侧边栏 — 固定在右侧,显示年月刻度线和一个可拖动的指示器。
//  交互与 Telegram / Apple Photos 相册的时间轴一致:
//    - 悬停显示日期气泡
//    - 拖动时实时滚动 + 圆点跟手
//    - 拖动结束跳转
//
//  与 vue/src/components/DateScrubber.vue 同构,差异:mac 上 tooltip 用 .overlay
//  浮在组件之外,避免被 frame 宽度裁切;currentDate 改为单向传入(拖动期间走 draggingDate 本地覆盖)。
//

import SwiftUI

struct DateScrubber: View {
    let timeline: [TimelineEntry]
    let minDate: Date
    let maxDate: Date
    /// 由外部传入(基于主网格 scrollTop 派生);拖动期间被 draggingDate 覆盖显示。
    let currentDate: Date

    var onJump: ((Date) -> Void)? = nil
    var onJumpFinal: ((Date) -> Void)? = nil

    // 内部状态
    @State private var dragging = false
    @State private var hovering = false
    @State private var tooltipDate: Date? = nil
    @State private var tooltipY: CGFloat = 0
    /// 拖动期间用这个临时覆盖外部 currentDate,保证圆点每帧跟手指。
    @State private var draggingDate: Date? = nil

    // 节流:onJump 每帧最多一次
    @State private var pendingJumpDate: Date? = nil
    @State private var jumpInFlight: Bool = false

    private let barWidth: CGFloat = 28
    private let yearColumnWidth: CGFloat = 26
    private let totalWidth: CGFloat = 28 + 26 + 8  // bar + 年标签列 + 一点右内边距

    /// 圆点显示的日期 —— 拖动期间走本地覆盖,平时用外部传入。
    private var displayDate: Date {
        draggingDate ?? currentDate
    }

    var body: some View {
        GeometryReader { geo in
            let height = geo.size.height

            ZStack(alignment: .topLeading) {
                HStack(spacing: 0) {
                    // 左侧年份标签列(防重叠折叠)
                    if timeline.count >= 2 {
                        yearLabelsColumn(height: height)
                            .frame(width: yearColumnWidth)
                    } else {
                        Color.clear.frame(width: yearColumnWidth)
                    }

                    // 右侧刻度轨道
                    ZStack(alignment: .topTrailing) {
                        // 中心轴线
                        Rectangle()
                            .fill(Color.gray.opacity(0.3))
                            .frame(width: 1)
                            .padding(.horizontal, 1.5)

                        // 月刻度(短)
                        ForEach(monthTicks, id: \.self) { pct in
                            Rectangle()
                                .fill(Color.gray.opacity(0.4))
                                .frame(width: 4, height: 1)
                                .offset(x: -6)
                                .position(x: barWidth - 3, y: height * pct / 100)
                        }

                        // 年刻度(长)
                        ForEach(yearTicks, id: \.self) { pct in
                            Rectangle()
                                .fill(Color.gray.opacity(0.6))
                                .frame(width: 8, height: 1.5)
                                .offset(x: -10)
                                .position(x: barWidth - 5, y: height * pct / 100)
                        }

                        // 指示器
                        indicatorView(height: height)
                    }
                    .frame(width: barWidth)
                    .contentShape(Rectangle())
                    .gesture(dragGesture(height: height))
                    .onContinuousHover { phase in
                        switch phase {
                        case .active(let p):
                            hovering = true
                            if !dragging {
                                tooltipY = clamp(p.y, 20, height - 20)
                                tooltipDate = percentToDate(clamp01(p.y / height) * 100)
                            }
                        case .ended:
                            hovering = false
                            if !dragging { tooltipDate = nil }
                        }
                    }
                }

                // tooltip 浮层 —— 放在 ZStack 顶,浮在 scrubber 之外,
                // 通过负 x offset 显示在 scrubber 左侧,不受 totalWidth 限制
                if (hovering || dragging), let date = tooltipDate {
                    tooltipBubble(date: date, height: height)
                        .position(x: -32, y: tooltipY)
                }
            }
        }
        .frame(width: totalWidth)
    }

    // MARK: - 刻度计算

    private var totalRangeSec: Double {
        max(maxDate.timeIntervalSince(minDate), 1)
    }

    private func dateToPercent(_ date: Date) -> Double {
        ((maxDate.timeIntervalSince(date) / totalRangeSec) * 100)
    }

    private func percentToDate(_ pct: Double) -> Date {
        let t = totalRangeSec * (pct / 100)
        return maxDate.addingTimeInterval(-t)
    }

    private var indicatorPercent: Double {
        clamp01(dateToPercent(displayDate) / 100) * 100
    }

    private var monthTicks: [Double] {
        timeline.compactMap { entry in
            guard let d = Calendar.current.date(from: DateComponents(year: entry.year, month: entry.month, day: entry.day)) else { return nil }
            return max(0, min(100, dateToPercent(d)))
        }
    }

    private var yearTicks: [Double] {
        guard !timeline.isEmpty else { return [] }
        let years = Set(timeline.map { $0.year })
        return years.sorted(by: >).compactMap { year in
            guard let d = Calendar.current.date(from: DateComponents(year: year, month: 1, day: 1)) else { return nil }
            return max(0, min(100, dateToPercent(d)))
        }
    }

    /// 年份文字标签(防重叠折叠:相邻 top% 差 < 8 时只保留较新一年)。
    private var yearLabels: [(year: Int, top: Double)] {
        guard !timeline.isEmpty else { return [] }
        let years = Set(timeline.map { $0.year }).sorted(by: >)  // 新 → 旧
        let raw: [(year: Int, top: Double)] = years.compactMap { year in
            guard let d = Calendar.current.date(from: DateComponents(year: year, month: 1, day: 1)) else { return nil }
            return (year, max(0, min(100, dateToPercent(d))))
        }
        // 已按新→旧排,top% 是从小到大(maxDate=0%)。直接顺序遍历,
        // 与已 kept 的最后一个 top 差 < 8% 就丢掉。
        var kept: [(year: Int, top: Double)] = []
        for item in raw {
            if let last = kept.last, item.top - last.top < 8 { continue }
            kept.append(item)
        }
        return kept
    }

    // MARK: - 子视图

    private func yearLabelsColumn(height: CGFloat) -> some View {
        ZStack(alignment: .topTrailing) {
            ForEach(yearLabels, id: \.year) { label in
                Text("\(label.year)")
                    .font(.system(size: 10, weight: .medium))
                    .foregroundColor(.secondary)
                    .lineLimit(1)
                    .minimumScaleFactor(0.5)
                    .position(
                        x: yearColumnWidth - 13,
                        y: height * label.top / 100
                    )
            }
        }
    }

    private func indicatorView(height: CGFloat) -> some View {
        let y = height * indicatorPercent / 100
        return ZStack(alignment: .trailing) {
            Rectangle()
                .fill(Color.accentColor)
                .frame(width: 3, height: 1)
                .offset(x: -6)
            Circle()
                .fill(Color.accentColor)
                .frame(width: 6, height: 6)
                .shadow(color: Color.accentColor.opacity(0.5), radius: 3)
        }
        .position(x: barWidth - 3, y: y)
        .animation(dragging ? nil : .easeOut(duration: 0.2), value: indicatorPercent)
    }

    private func tooltipBubble(date: Date, height: CGFloat) -> some View {
        let f = DateFormatter()
        f.dateFormat = "yyyy年M月d日"
        let label = f.string(from: date)
        return Text(label)
            .font(.system(size: 11, weight: .medium))
            .foregroundColor(.white)
            .padding(.horizontal, 8)
            .padding(.vertical, 4)
            .background(.black.opacity(0.7))
            .cornerRadius(6)
            .fixedSize()
    }

    // MARK: - 手势

    private func dragGesture(height: CGFloat) -> some Gesture {
        DragGesture(minimumDistance: 0)
            .onChanged { value in
                dragging = true
                let pct = clamp01(value.location.y / height) * 100
                let date = percentToDate(pct)
                // 每帧都更新:tooltip + 本地圆点覆盖
                tooltipDate = date
                tooltipY = clamp(value.location.y, 20, height - 20)
                draggingDate = date
                scheduleJump(date)
            }
            .onEnded { value in
                let pct = clamp01(value.location.y / height) * 100
                let date = percentToDate(pct)
                draggingDate = date  // 给外部更新留一拍,避免回弹
                dragging = false
                tooltipDate = nil
                onJumpFinal?(date)
                // 下一拍清空,让外部 currentDate 接管
                DispatchQueue.main.asyncAfter(deadline: .now() + 0.05) {
                    draggingDate = nil
                }
            }
    }

    /// onJump 节流:每帧最多触发一次。用 Task.yield 让出当前帧。
    private func scheduleJump(_ date: Date) {
        pendingJumpDate = date
        if jumpInFlight { return }
        jumpInFlight = true
        Task { @MainActor in
            await Task.yield()
            jumpInFlight = false
            if let d = pendingJumpDate {
                onJump?(d)
                pendingJumpDate = nil
            }
        }
    }
}

// MARK: - 小工具

private func clamp01(_ v: Double) -> Double { max(0, min(1, v)) }
private func clamp01(_ v: CGFloat) -> CGFloat { max(0, min(1, v)) }
private func clamp(_ v: CGFloat, _ lo: CGFloat, _ hi: CGFloat) -> CGFloat { max(lo, min(hi, v)) }

#Preview {
    let entries = [
        TimelineEntry(year: 2026, month: 6, day: 7, count: 12),
        TimelineEntry(year: 2026, month: 6, day: 5, count: 8),
        TimelineEntry(year: 2026, month: 5, day: 20, count: 25),
        TimelineEntry(year: 2026, month: 4, day: 1, count: 3),
    ]
    return HStack {
        Spacer()
        DateScrubber(
            timeline: entries,
            minDate: Calendar.current.date(from: DateComponents(year: 2026, month: 4, day: 1))!,
            maxDate: Date(),
            currentDate: Date()
        )
    }
    .frame(height: 400)
}
