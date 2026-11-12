"""UI translations (English / 简体中文) for the Streamlit dashboard.

Usage:  t("key", **format_args)  -> string in the current language.
The current language lives in st.session_state["lang"] ("en" or "zh").
Notifications and the alert log stay in English (they are produced by monitor.py).
"""
from __future__ import annotations

import streamlit as st

LANGS = ("en", "zh")

TEXT: dict[str, tuple[str, str]] = {
    # ---- header / price cards ---------------------------------------------------
    "page_title": ("Real-Time Investment Monitoring & Alert System", "实时投资监控与提醒系统"),
    "subtitle": ("SPY & QQQ · live prices, risk metrics and custom alerts · data: Yahoo Finance (yfinance)",
                 "SPY & QQQ · 实时价格、风险指标与自定义提醒 · 数据来源：Yahoo Finance (yfinance)"),
    "toggle": ("🌐 中文", "🌐 English"),
    "toggle_help": ("Switch language", "切换语言"),
    "market_open": ("🟢 US market OPEN", "🟢 美股 开盘中"),
    "market_closed": ("🔴 US market CLOSED", "🔴 美股 已休市"),
    "quote_unavailable": ("{sym}: live quote unavailable (Yahoo may be rate-limiting). Retrying automatically in 60s.",
                          "{sym}：暂时无法获取实时报价（Yahoo 可能在限流），60 秒后自动重试。"),
    "ohlc": ("Open {o:.2f} · High {h:.2f} · Low {l:.2f} · Prev close {p:.2f}",
             "开盘 {o:.2f} · 最高 {h:.2f} · 最低 {l:.2f} · 昨收 {p:.2f}"),
    "updated": ("Updated {ts} ET", "更新于 {ts}（美东时间）"),
    "ny_time": ("New York time: {ts}", "纽约时间：{ts}"),
    "session_note": ("Regular session Mon–Fri 09:30–16:00 ET (holidays not considered). Cards refresh every 60 seconds.",
                     "常规交易时段：美东时间周一至周五 09:30–16:00（未考虑节假日）。价格卡片每 60 秒自动刷新。"),
    "refresh": ("🔄 Refresh now", "🔄 立即刷新"),
    "loading_history": ("Loading 10-year history…", "正在加载 10 年历史数据…"),
    # ---- tabs ---------------------------------------------------------------------
    "tab_chart": ("📈 Price Chart", "📈 价格走势"),
    "tab_dd": ("📉 Drawdown", "📉 回撤"),
    "tab_cmp": ("⚖️ SPY vs QQQ", "⚖️ SPY 对比 QQQ"),
    "tab_events": ("🩹 Declines & Recoveries", "🩹 下跌与恢复"),
    "tab_rules": ("🔔 Alert Rules", "🔔 提醒规则"),
    "tab_log": ("🧾 Alert Log", "🧾 提醒记录"),
    # ---- price chart --------------------------------------------------------------
    "symbol": ("Symbol", "标的"),
    "range": ("Range", "时间范围"),
    "chart_type": ("Chart type", "图表类型"),
    "Line": ("Line", "折线"),
    "Candlestick": ("Candlestick", "K 线"),
    "history_unavailable": ("Historical data is unavailable right now. Please try again in a minute.",
                            "暂时无法获取历史数据，请稍后再试。"),
    "close_series": ("{sym} close", "{sym} 收盘价"),
    "price_axis": ("Price (USD, dividend-adjusted)", "价格（美元，已复权）"),
    "vs_ma50": ("vs MA50", "相对 MA50"),
    "vs_ma200": ("vs MA200", "相对 MA200"),
    "dd_ath": ("Drawdown from ATH", "距历史高点回撤"),
    "max_dd": ("10Y max drawdown", "10 年最大回撤"),
    "trough_on": ("Trough on {d}", "谷底日期：{d}"),
    "vol_20_1y": ("Volatility 20D / 1Y", "波动率 20日 / 1年"),
    "vol_help": ("Annualised standard deviation of daily returns", "日收益率的年化标准差"),
    "trend": ("Trend regime", "趋势状态"),
    "golden": ("Golden", "金叉"),
    "death": ("Death", "死叉"),
    "trend_help": ("MA50 {rel} MA200; last cross: {typ} on {d}", "MA50 {rel} MA200；最近一次交叉：{d} {typ}"),
    "return_p": ("Return {p}", "{p} 收益率"),
    # ---- drawdown -----------------------------------------------------------------
    "dd_title": ("Distance from all-time high (10 years)", "距历史最高点的回撤（10 年）"),
    "dd_caption": ("0% = at a record high. The deeper the line, the larger the decline from the prior peak.",
                   "0% 表示处于历史新高。曲线越深，表示距前高的跌幅越大。"),
    "sym_unavailable": ("{sym} history unavailable.", "{sym} 历史数据暂不可用。"),
    "correction": ("-10% correction", "-10% 回调"),
    "bear": ("-20% bear market", "-20% 熊市"),
    "dd_axis": ("Drawdown (%)", "回撤（%）"),
    # ---- comparison ---------------------------------------------------------------
    "cmp_unavailable": ("Comparison needs both histories; one is unavailable right now.",
                        "对比需要两只标的的历史数据，目前有一只暂不可用。"),
    "norm_title": ("Normalised growth (start of range = 100)", "归一化收益对比（区间起点 = 100）"),
    "growth_axis": ("Growth of 100", "100 的增长"),
    "risk_title": ("Risk & return comparison", "风险与收益对比"),
    "vol20_ann": ("Volatility 20D (ann.)", "20 日波动率（年化）"),
    "vol1y_ann": ("Volatility 1Y (ann.)", "1 年波动率（年化）"),
    "vol10y_ann": ("Volatility 10Y (ann.)", "10 年波动率（年化）"),
    "cur_dd": ("Current drawdown", "当前回撤"),
    "rollvol_title": ("Rolling 20-day volatility (annualised)", "20 日滚动波动率（年化）"),
    "vol_axis": ("Volatility (%)", "波动率（%）"),
    # ---- declines & recoveries ----------------------------------------------------
    "ev_title": ("Historical declines and how long recovery took", "历史下跌事件及恢复用时"),
    "ev_caption": ("An episode runs from a peak to the first close back at that peak. 'Days' are trading days. "
                   "'Days to Recover' counts from the trough to the recovery date.",
                   "每个事件从前高开始，到收盘价首次回到该前高为止。天数均为交易日。"
                   "「恢复天数」从谷底算到恢复日。"),
    "ev_header": ("**Declines > {th}%** — {n} episode(s)", "**跌幅超过 {th}%** — 共 {n} 次"),
    "ev_none": ("None in the last 10 years.", "近 10 年内没有。"),
    "Peak Date": ("Peak Date", "前高日期"),
    "Trough Date": ("Trough Date", "谷底日期"),
    "Max Drawdown %": ("Max Drawdown %", "最大跌幅 %"),
    "Recovery Date": ("Recovery Date", "恢复日期"),
    "Days Peak→Trough": ("Days Peak→Trough", "前高→谷底天数"),
    "Days to Recover": ("Days to Recover", "恢复天数"),
    "Not recovered": ("Not recovered", "未恢复"),
    # ---- rules --------------------------------------------------------------------
    "rules_title": ("Alert rules", "提醒规则"),
    "rules_caption": ("Edit cells directly, add rows with ＋, delete by selecting rows and pressing 🗑. "
                      "Click **Save rules** to write rules.json — the background monitor picks up changes on its "
                      "next cycle. 'Value' is required for Price / Daily drop / Drawdown rules. "
                      "'Breaks below/above' and cross rules fire only on the day the line is crossed.",
                      "直接双击单元格编辑，用 ＋ 添加行，选中行后点 🗑 删除。点击 **保存规则** 写入 rules.json，"
                      "后台监控会在下一轮检查时自动读取。价格 / 单日跌幅 / 回撤类规则必须填写数值；"
                      "「跌破 / 站上」均线和金叉、死叉规则只在穿越当天触发。"),
    "col_enabled": ("Enabled", "启用"),
    "col_rule": ("Rule type", "规则类型"),
    "col_value": ("Value (X)", "数值 (X)"),
    "col_note": ("Note", "备注"),
    "save_rules": ("💾 Save rules", "💾 保存规则"),
    "err_required": ("Row {i}: symbol and rule type are required.", "第 {i} 行：标的和规则类型为必填项。"),
    "err_value": ("Row {i} ({rule}): please enter a value.", "第 {i} 行（{rule}）：请填写数值。"),
    "not_saved": ("Not saved:", "未保存："),
    "saved_rules": ("Saved {n} rule(s) to rules.json.", "已保存 {n} 条规则到 rules.json。"),
    "live_status": ("Live status", "实时状态"),
    "st_enabled": ("Enabled", "启用"),
    "st_rule": ("Rule", "规则"),
    "st_met": ("Condition met now", "当前是否满足"),
    "st_note": ("Note", "备注"),
    "yes": ("🔔 YES", "🔔 是"),
    "no": ("no", "否"),
    "data_unavailable": ("data unavailable", "数据不可用"),
    "check_now": ("▶ Check enabled rules now (sends notifications)", "▶ 立即检查已启用的规则（会发送通知）"),
    "fired_n": ("{n} new alert(s) sent.", "已发送 {n} 条新提醒。"),
    "fired_none": ("No new alerts (nothing met, or already notified today).", "没有新提醒（条件未满足，或今天已经通知过）。"),
    "notif_title": ("Notification settings", "通知设置"),
    "ntfy_topic": ("ntfy.sh topic (leave empty to disable phone push)", "ntfy.sh 主题名（留空则不推送到手机）"),
    "ntfy_help": ("Pick a long, hard-to-guess name, e.g. spyqqq-alerts-7f3k9. Install the ntfy app and subscribe to the same topic.",
                  "请起一个较长、不易被猜到的名字，例如 spyqqq-alerts-7f3k9。安装 ntfy App 并订阅同名主题。"),
    "interval": ("Monitor check interval (minutes)", "后台检查间隔（分钟）"),
    "desktop": ("Windows desktop notifications", "Windows 桌面通知"),
    "save_settings": ("Save settings", "保存设置"),
    "settings_saved": ("Settings saved.", "设置已保存。"),
    "test_notif": ("🔔 Send test notification", "🔔 发送测试通知"),
    "test_result": ("Desktop: {d} · ntfy: {n}", "桌面通知：{d} · ntfy：{n}"),
    "sent": ("sent", "已发送"),
    "failed": ("failed", "失败"),
    "not_configured": ("skipped (no topic set — enter one above to enable phone push)",
                       "未启用（主题名为空，在上方填写后即可推送到手机）"),
    "ntfy_failed": ("failed — check the topic name and your network", "发送失败，请检查主题名和网络"),
    # ---- log ----------------------------------------------------------------------
    "log_title": ("Recent alerts", "最近的提醒"),
    "log_empty": ("No alerts have been triggered yet. Start `python monitor.py` to monitor in the background.",
                  "还没有触发过提醒。运行 `python monitor.py` 开始后台监控。"),
    "log_time": ("Time (ET)", "时间（美东）"),
    "log_price": ("Price", "价格"),
    "log_chg": ("Day chg", "当日涨跌"),
    "log_dd": ("Drawdown", "回撤"),
    "log_vol": ("20D vol", "20 日波动率"),
    "download_csv": ("Download CSV", "下载 CSV"),
    "log_note": ("Rule text in the log is recorded in English by the monitor.", "记录中的规则文字由后台监控以英文写入。"),
    # ---- footer -------------------------------------------------------------------
    "disclaimer": ("⚠️ Disclaimer: This tool is for data monitoring and educational purposes only. "
                   "It does not constitute investment advice.",
                   "⚠️ 免责声明：本工具仅用于数据监控和学习，不构成任何投资建议。"),
}

# Chinese labels for rule types (English labels live in rules.RULE_TYPES).
RULE_LABELS_ZH = {
    "price_below": "价格低于 X",
    "price_above": "价格高于 X",
    "daily_drop": "当日跌幅超过 X%",
    "drawdown": "距最高点回撤超过 X%",
    "cross_below_ma200": "跌破 MA200",
    "cross_above_ma200": "站上 MA200",
    "cross_below_ma50": "跌破 MA50",
    "cross_above_ma50": "站上 MA50",
    "golden_cross": "金叉（MA50 上穿 MA200）",
    "death_cross": "死叉（MA50 下穿 MA200）",
}

WEEKDAYS_ZH = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"]


def lang() -> str:
    return st.session_state.get("lang", "en")


def t(key: str, **kwargs) -> str:
    """Translate `key` into the current language and apply str.format(**kwargs)."""
    pair = TEXT.get(key)
    if pair is None:
        return key
    s = pair[LANGS.index(lang())]
    return s.format(**kwargs) if kwargs else s


def rule_label(rule_type: str) -> str:
    """Localised label for a rule type."""
    from .rules import RULE_TYPES
    if lang() == "zh":
        return RULE_LABELS_ZH.get(rule_type, rule_type)
    return RULE_TYPES.get(rule_type, (rule_type,))[0]


def describe_rule(rule: dict) -> str:
    """Localised version of rules.describe, e.g. 'SPY：价格低于 500'."""
    from .rules import RULE_TYPES
    label = rule_label(rule["type"])
    if RULE_TYPES.get(rule["type"], ("", False))[1] and rule.get("value") is not None:
        label = label.replace("X", f"{rule['value']:g}")
    sep = "：" if lang() == "zh" else ": "
    return f"{rule['symbol']}{sep}{label}"


def weekday(ts) -> str:
    return WEEKDAYS_ZH[ts.weekday()] if lang() == "zh" else ts.strftime("%a")
