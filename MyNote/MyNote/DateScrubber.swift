//
//  DateScrubber.swift
//  MyNote
//
//  时间轴侧边栏 — 固定在右侧,显示年月刻度线和一个可拖动的指示器。
//  交互与 Telegram/Photos 相册的时间轴一致:
//    - 悬停显示日期气泡
//    - 拖动时实时滚动
//    - 拖动结束跳转
//

import SwiftUI

struct DateScrubber: View {
    let timeline: [TimelineEntry]
    let minDate: Date
    let maxDate: Date
    @Binding var currentDate: Date

    var onJump: ((Date) -> Void)? = nil
    var onJumpFinal: ((Date) -> Void)? = nil

    // 内部状态
    @State private var dragging = false
    @State private var hovering = false
    @State private var tooltipDate: Date? = nil
    @State private var tooltipY: CGFloat = 0

    private let barWidth: CGFloat = 28

    var body: some View {
        GeometryReader { geo in
            let height = geo.size.height

            HStack(spacing: 0) {
                // 左侧年份标签列
                if timeline.count >= 2 {
                    yearLabelsColumn(height: height)
                        .frame(width: 26)
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

                    // 指示器(当前日期)
                    indicatorView(height: height)

                    // 拖动/悬停气泡
                    if (hovering || dragging) && tooltipDate != nil {
                        tooltipBubble(height: height)
                    }
                }
                .frame(width: barWidth)
                // 透明 HitTest 层用于拖动
                .contentShape(Rectangle())
                .gesture(dragGesture(height: height))
            }
        }
        .frame(width: barWidth + 34)
    }

    // MARK: - 刻度计算

    private var totalRangeMs: Double {
        max(maxDate.timeIntervalSince(minDate), 1)
    }

    private func dateToPercent(_ date: Date) -> Double {
        ((maxDate.timeIntervalSince(date) / totalRangeMs) * 100)
    }

    private func percentToDate(_ pct: Double) -> Date {
        let t = totalRangeMs * (pct / 100)
        return maxDate.addingTimeInterval(-t)
    }

    private var indicatorPercent: Double {
        dateToPercent(currentDate)
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

    private var yearLabels: [(year: Int, top: Double)] {
        guard !timeline.isEmpty else { return [] }
        let years = Set(timeline.map { $0.year }).sorted(by: >)
        return years.compactMap { year in
            guard let d = Calendar.current.date(from: DateComponents(year: year, month: 1, day: 1)) else { return nil }
            let pct = max(0, min(100, dateToPercent(d)))
            return (year, pct)
        }
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
                        x: 13,
                        y: height * label.top / 100
                    )
            }
        }
    }

    private func indicatorView(height: CGFloat) -> some View {
        let y = height * max(0, min(100, indicatorPercent)) / 100
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
        .animation(.easeOut(duration: 0.2), value: indicatorPercent)
    }

    private func tooltipBubble(height: CGFloat) -> some View {
        let label: String = {
            guard let date = tooltipDate else { return "" }
            let formatter = DateFormatter()
            formatter.dateFormat = "yyyy年M月d日"
            return formatter.string(from: date)
        }()
        return Text(label)
            .font(.system(size: 11, weight: .medium))
            .foregroundColor(.white)
            .padding(.horizontal, 8)
            .padding(.vertical, 4)
            .background(.black.opacity(0.7))
            .cornerRadius(6)
            .position(x: barWidth + 20, y: min(max(tooltipY, 20), height - 20))
    }

    // MARK: - 手势

    private func dragGesture(height: CGFloat) -> some Gesture {
        DragGesture(minimumDistance: 0)
            .onChanged { value in
                let wasDragging = dragging
                dragging = true
                let pct = max(0, min(100, value.location.y / height * 100))
                tooltipDate = percentToDate(pct)
                tooltipY = value.location.y
                if !wasDragging {
                    onJump?(tooltipDate!)
                }
            }
            .onEnded { value in
                let pct = max(0, min(100, value.location.y / height * 100))
                let date = percentToDate(pct)
                currentDate = date
                onJumpFinal?(date)
                dragging = false
            }
    }
}

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
            currentDate: .constant(Date())
        )
    }
    .frame(height: 400)
}
