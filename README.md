# Real-Time Investment Monitoring & Alert System

A personal dashboard and background monitor for **SPY** (S&P 500) and **QQQ** (Nasdaq-100).
It tracks live prices and 10 years of daily history, computes trend and risk indicators,
and alerts you when your own price targets or risk thresholds are hit.
Alerts arrive as a Windows desktop notification and, optionally, as a phone push via ntfy.sh.

> **Disclaimer:** This tool is for data monitoring and educational purposes only. It does not constitute investment advice.

## 🚀 快速上手：怎么打开（中文）

> 环境和依赖已经装好（`.venv` 文件夹已存在）。每次使用只需要做下面几步。

### 第 1 步：在 VS Code 里打开终端
1. 用 VS Code 打开文件夹 `C:\Users\14789\Desktop\ClaudeCodeProgram\stockprice`。
2. 菜单栏点 **终端 (Terminal) → 新建终端 (New Terminal)**，或按快捷键 ``Ctrl + ` ``。

### 第 2 步：启动仪表盘（网页）
在终端里依次输入下面三行，每行输完按回车：

```powershell
cd C:\Users\14789\Desktop\ClaudeCodeProgram\stockprice
.\.venv\Scripts\Activate.ps1
streamlit run app.py
```

- 第二行运行成功后，命令行最前面会出现 `(.venv)`，说明已经进入虚拟环境。
- 第三行运行后，浏览器会**自动打开**仪表盘。如果没有自动打开，就手动在浏览器地址栏输入 **http://localhost:8501**。
- 网页右上角的 **🌐 中文 / 🌐 English** 按钮可以切换语言。
- ⚠️ 用网页期间**不要关闭这个终端**。关掉终端，网页就停止工作了。

### 第 3 步（可选）：启动后台监控
后台监控在关掉网页后也能继续检查你的提醒规则，并弹出桌面通知。
点终端面板右上角的 **＋** 新开一个终端，再输入：

```powershell
cd C:\Users\14789\Desktop\ClaudeCodeProgram\stockprice
.\.venv\Scripts\Activate.ps1
python monitor.py
```

它只在美股交易时段（北京时间约 22:30–次日 05:00，夏令时提前 1 小时）实际检查，其他时间会显示 `Market closed - skipping check.`，这是正常的。

### 如何关闭
在对应的终端里按 **`Ctrl + C`** 即可停止仪表盘或后台监控。

### 常见问题
| 问题 | 解决办法 |
|---|---|
| 第二行报错 “**禁止运行脚本** / running scripts is disabled” | 先运行一次 `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned`，输入 `Y` 确认，再重试。或者跳过第二行，把第三行改成 `.\.venv\Scripts\streamlit.exe run app.py`（监控用 `.\.venv\Scripts\python.exe monitor.py`） |
| 提示 `streamlit` 不是内部或外部命令 | 说明没进入虚拟环境，检查第二行是否成功（前面有没有 `(.venv)`） |
| 端口被占用 / 想同时开两个 | `streamlit run app.py --server.port 8502`，然后访问 http://localhost:8502 |
| 价格卡片显示 “live quote unavailable” | Yahoo 临时限流或网络问题，等 1 分钟会自动重试，或点「立即刷新」 |
| 想测试桌面通知能不能弹出 | 网页里进入「🔔 提醒规则」页，点「🔔 发送测试通知」 |

## Features

| Area | What you get |
|---|---|
| Live prices | Price cards for SPY & QQQ: price, change, % change, OHLC, update time, market open/closed. Auto-refresh every 60 s, plus a manual refresh button |
| Price chart | 1M / 6M / 1Y / 5Y / 10Y, line or candlestick, with MA50 / MA200 overlay |
| Indicators | Daily change, MA50/MA200 and % deviation, drawdown from high, 10-year max drawdown, 20-day and 1-year annualised volatility, 1M/3M/1Y/5Y/10Y returns, golden/death cross |
| Drawdown chart | Distance from all-time high over 10 years, with −10% / −20% reference lines |
| SPY vs QQQ | Normalised growth chart, risk/return table, rolling volatility |
| Declines & recoveries | Every decline greater than 10% and 20%: peak date, trough date, max loss, recovery date, and how many trading days the recovery took (or "Not recovered") |
| Alert rules | Add, edit, delete, enable or disable rules in the dashboard. They are saved to `rules.json` |
| Background monitor | `monitor.py` checks the rules every 5 min during US market hours, even when the dashboard is closed |
| Alert log | Every triggered alert is stored in `data/alerts_log.csv` and shown in the dashboard |

### Supported rule types

| Rule | Fires when |
|---|---|
| Price below / above X | the live price is below / above X |
| Daily drop exceeds X% | today's change is ≤ −X% |
| Drawdown from high exceeds X% | the price is more than X% below its 10-year high |
| Breaks below / above MA200 (or MA50) | **the day** the price crosses the moving average (yesterday's close was on the other side) |
| Golden cross / Death cross | **the day** MA50 crosses above / below MA200 |

Each rule notifies **at most once per day**. The notification shows the symbol, the rule, the price, today's % change, the deviation from MA200 and the current drawdown.

## Tech stack

Python 3.11+ · yfinance (no API key) · Streamlit · Plotly · Pandas · plyer (desktop notifications) · ntfy.sh (phone push)

## Installation (Windows)

```powershell
cd C:\Users\<you>\Desktop\ClaudeCodeProgram\stockprice
py -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

> If PowerShell blocks `Activate.ps1`, run `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned` once,
> or skip activation and call `.\.venv\Scripts\python.exe` directly.

Check that the data source works:

```powershell
python tests\test_fetch.py        # live price + history row count
python tests\test_indicators.py   # all SPY indicators + drawdown episodes
```

## Start the dashboard

```powershell
.\.venv\Scripts\Activate.ps1
streamlit run app.py
```

The dashboard opens at http://localhost:8501.
Use the **🌐 中文 / 🌐 English** button in the top-right corner to switch the UI language
(the choice is kept in the URL as `?lang=zh`, so it survives a page refresh).
All UI text lives in `src/i18n.py`.

## Start the background monitor

Open a **second** terminal:

```powershell
.\.venv\Scripts\Activate.ps1
python monitor.py
```

| Command | Purpose |
|---|---|
| `python monitor.py` | Run continuously; checks only Mon–Fri 09:30–16:00 New York time |
| `python monitor.py --interval 2` | Check every 2 minutes (minimum 1) |
| `python monitor.py --once --force` | Run one check right now, even if the market is closed (for testing) |

Stop the monitor with `Ctrl+C`. Its log is written to `data/monitor.log`.
The monitor re-reads `rules.json` every cycle, so rule changes made in the dashboard apply without a restart.
If the network or Yahoo fails, it logs the error and tries again on the next cycle.

**Test that notifications work:** in the **Alert Rules** tab, enable the rule *"SPY: Price above 1"*, click **Save rules**, then click **Check enabled rules now** (or run `python monitor.py --once --force`).
A Windows notification should pop up. Disable the rule again afterwards.

## Phone push notifications (ntfy.sh)

1. Install the **ntfy** app (Android / iOS), or open https://ntfy.sh in a browser.
2. Choose a long, hard-to-guess topic name, for example `spyqqq-alerts-7f3k9x`. Topics are public, so anyone who knows the name can read it.
3. In the app, tap **Subscribe to topic** and enter that name.
4. In the dashboard, go to **Alert Rules → Notification settings**, paste the same topic name and click **Save settings**.
5. Click **Send test notification**. Your phone should receive it.

Leave the topic empty to turn off phone push.

## Project structure

```
stockprice/
├─ app.py              # Streamlit dashboard (entry point)
├─ monitor.py          # Background monitor: checks rules, sends notifications
├─ src/
│  ├─ data.py          # yfinance access: live quote, 10y history (CSV cache), market hours, retries
│  ├─ indicators.py    # MAs, drawdown, volatility, returns, crosses, decline/recovery episodes
│  ├─ rules.py         # Rule types, rules.json read/write, evaluation, alert log, de-duplication
│  └─ notify.py        # Windows desktop notification + ntfy.sh push
├─ tests/
│  ├─ test_fetch.py       # Stage-1 data smoke test
│  └─ test_indicators.py  # Prints SPY indicators
├─ data/               # (git-ignored) history cache, alerts_log.csv, monitor.log
├─ rules.json          # Your alert rules + notification settings
├─ requirements.txt
└─ README.md
```

## Notes and limitations

- **Data:** Yahoo Finance via yfinance. Quotes may be delayed by a few seconds, and Yahoo sometimes rate-limits. Every request retries with back-off. If a request still fails, the dashboard shows a warning instead of crashing, and a stale history cache is used if one exists.
- **Request rate:** live quotes are cached for 60 s. Daily history is downloaded at most once per day and stored in `data/<SYMBOL>_history.csv`.
- **Prices:** history is dividend-adjusted (`auto_adjust=True`), so long-term returns include dividends.
- **Market hours:** US exchange holidays are not handled yet. On a holiday the monitor still runs, but prices don't change.
