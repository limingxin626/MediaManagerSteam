//
//  RelativeTimeFormatter.swift
//  MyNote
//
//  把 ISO created_at 字符串转成「2 小时前」「昨天」「3 天前」「2026-05-29」
//  的相对时间。给消息卡用,纯函数,无副作用。
//

import Foundation

enum RelativeTimeFormatter {
    /// 输入 ISO 字符串(对齐 Message.createdAt / MessageISO.format 的格式),
    /// 输出短中文相对时间。
    static func format(_ iso: String, now: Date = Date()) -> String {
        guard let date = MessageISO.formatter.date(from: iso) else { return iso }
        return format(date, now: now)
    }

    static func format(_ date: Date, now: Date = Date()) -> String {
        let interval = now.timeIntervalSince(date)

        // 1 分钟内 → "刚刚"
        if interval < 60 {
            return "刚刚"
        }
        // 1 小时内 → "N 分钟前"
        if interval < 3600 {
            let m = Int(interval / 60)
            return "\(m) 分钟前"
        }
        // 同一天 → "N 小时前"
        if Calendar.current.isDateInToday(date) {
            let h = Int(interval / 3600)
            return "\(h) 小时前"
        }
        // 昨天 → "昨天 HH:mm"
        if Calendar.current.isDateInYesterday(date) {
            return "昨天 \(timeOfDay(date))"
        }
        // 7 天内 → "N 天前"
        if interval < 7 * 86400 {
            let d = Int(interval / 86400)
            return "\(d) 天前"
        }
        // 同年 → "M月D日"
        let cal = Calendar.current
        if cal.component(.year, from: date) == cal.component(.year, from: now) {
            return String(format: "%d月%d日", cal.component(.month, from: date), cal.component(.day, from: date))
        }
        // 跨年 → "YYYY-M-D"
        return String(format: "%d-%d-%d",
                      cal.component(.year, from: date),
                      cal.component(.month, from: date),
                      cal.component(.day, from: date))
    }

    private static func timeOfDay(_ date: Date) -> String {
        let cal = Calendar.current
        return String(format: "%02d:%02d",
                      cal.component(.hour, from: date),
                      cal.component(.minute, from: date))
    }
}
