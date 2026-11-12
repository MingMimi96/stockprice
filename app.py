"""Real-Time Investment Monitoring & Alert System — Streamlit dashboard.

Run with:  streamlit run app.py
UI language (English / 中文) is toggled with the button in the top-right corner.
"""
from __future__ import annotations

import pandas as pd
import plotly.graph_objects as go
import streamlit as st
import streamlit.components.v1 as components

from src import data, indicators as ind, notify, rules
from src.i18n import LANGS, describe_rule, lang, rule_label, t, weekday

st.set_page_config(page_title="SPY & QQQ Monitor", page_icon="📈", layout="wide")

SYMBOLS = data.SYMBOLS
COLORS = {"SPY": "#2a78d6", "QQQ": "#eb6834"}          # categorical slots 1-2
MA_COLORS = {"MA50": "#eda100", "MA200": "#6250d6"}     # slots 4 and 7
UP, DOWN = "#1baf7a", "#e34948"
RANGES = {"1M": pd.DateOffset(months=1), "6M": pd.DateOffset(months=6),
          "1Y": pd.DateOffset(years=1), "5Y": pd.DateOffset(years=5),
          "10Y": pd.DateOffset(years=10)}

# --------------------------------------------------------------------------- #
# Language state: session_state is the source of truth; the URL (?lang=zh)
# remembers the choice across page reloads.
# --------------------------------------------------------------------------- #
if "lang" not in st.session_state:
    qp = st.query_params.get("lang", "en")
    st.session_state.lang = qp if qp in LANGS else "en"


def toggle_lang():
    new = "zh" if lang() == "en" else "en"
    st.session_state.lang = new
    st.query_params["lang"] = new


# --------------------------------------------------------------------------- #
# Cached data loaders (errors are returned, never raised, so the page survives)
# --------------------------------------------------------------------------- #
@st.cache_data(ttl=60, show_spinner=False)
def load_quote(symbol: str) -> dict | None:
    """Live quote, cached 60s so we never hit Yahoo more than once a minute."""
    try:
        return data.get_quote(symbol)
    except data.DataError:
        return None


@st.cache_data(ttl=3600, show_spinner=False)
def load_history(symbol: str) -> pd.DataFrame | None:
    try:
        return data.get_history(symbol)
    except data.DataError:
        return None


def live_frame(symbol: str) -> pd.DataFrame | None:
    """History with today's bar updated from the live quote, plus MA columns."""
    hist = load_history(symbol)
    if hist is None:
        return None
    return ind.add_moving_averages(data.merge_live_price(hist, load_quote(symbol)))


def fmt_pct(x: float) -> str:
    return f"{x:+.2f}%"


def base_layout(fig: go.Figure, height: int = 420, yaxis_title: str = "") -> go.Figure:
    fig.update_layout(height=height, margin=dict(l=10, r=10, t=30, b=10),
                      hovermode="x unified", yaxis_title=yaxis_title,
                      legend=dict(orientation="h", yanchor="bottom", y=1.02, x=0))
    return fig


# --------------------------------------------------------------------------- #
# 1. Header (title + language toggle top-right) and live price cards
# --------------------------------------------------------------------------- #
head_l, head_r = st.columns([6, 1], vertical_alignment="top")
with head_l:
    st.title(t("page_title"))
    st.caption(t("subtitle"))
with head_r:
    st.button(t("toggle"), on_click=toggle_lang, help=t("toggle_help"),
              key="lang_toggle", width="stretch")


@st.fragment(run_every=60)
def price_cards():
    top = st.columns([1, 1, 1])
    status = t("market_open") if data.is_market_open() else t("market_closed")
    for col, sym in zip(top[:2], SYMBOLS):
        q = load_quote(sym)
        with col.container(border=True):
            if q is None:
                st.warning(t("quote_unavailable", sym=sym))
                continue
            st.metric(sym, f"${q['price']:,.2f}",
                      f"{q['change']:+.2f} ({fmt_pct(q['change_pct'])})")
            st.caption(t("ohlc", o=q["open"], h=q["high"], l=q["low"], p=q["prev_close"]))
            st.caption(t("updated", ts=f"{q['fetched_at']:%Y-%m-%d %H:%M:%S}"))
    with top[2].container(border=True):
        st.markdown(f"### {status}")
        now = data.now_et()
        st.caption(t("ny_time", ts=f"{weekday(now)} {now:%Y-%m-%d %H:%M}"))
        st.caption(t("session_note"))
        if st.button(t("refresh"), width="stretch"):
            load_quote.clear()
            st.rerun()


price_cards()

# Streamlit always serves <html lang="en">, so Chrome/Edge offer to machine-translate
# the page and mangle text that is already Chinese. Set the real language and opt
# out of browser translation (the app has its own language toggle).
components.html(f"""<script>
  const root = window.parent.document.documentElement;
  root.setAttribute("lang", "{'zh-CN' if lang() == 'zh' else 'en'}");
  root.setAttribute("translate", "no");
  root.classList.add("notranslate");
</script>""", height=0)

tabs = st.tabs([t("tab_chart"), t("tab_dd"), t("tab_cmp"),
                t("tab_events"), t("tab_rules"), t("tab_log")])

# --------------------------------------------------------------------------- #
# 2. Price chart with MA50 / MA200
# --------------------------------------------------------------------------- #
with tabs[0]:
    c1, c2, c3 = st.columns([1, 2, 1])
    sym = c1.selectbox(t("symbol"), SYMBOLS, key="chart_sym")
    rng = c2.radio(t("range"), list(RANGES), index=2, horizontal=True, key="chart_rng")
    # Options are stable keys; only the displayed text is translated. The widget
    # gets a per-language key (its labels change), so the choice is kept in
    # session_state separately and survives a language switch.
    kinds = ["Line", "Candlestick"]
    kind = c3.radio(t("chart_type"), kinds, format_func=t, horizontal=True,
                    index=kinds.index(st.session_state.get("chart_kind", "Line")),
                    key=f"chart_kind_{lang()}")
    st.session_state.chart_kind = kind

    df = live_frame(sym)
    if df is None:
        st.error(t("history_unavailable"))
    else:
        # MAs were computed on the full history, so they are valid from the window start.
        view = df.loc[df.index[-1] - RANGES[rng]:]
        fig = go.Figure()
        if kind == "Candlestick":
            fig.add_trace(go.Candlestick(x=view.index, open=view["Open"], high=view["High"],
                                         low=view["Low"], close=view["Close"], name=sym,
                                         increasing_line_color=UP, decreasing_line_color=DOWN))
            fig.update_layout(xaxis_rangeslider_visible=False)
        else:
            fig.add_trace(go.Scatter(x=view.index, y=view["Close"], name=t("close_series", sym=sym),
                                     line=dict(color=COLORS[sym], width=2)))
        for ma in ["MA50", "MA200"]:
            fig.add_trace(go.Scatter(x=view.index, y=view[ma], name=ma,
                                     line=dict(color=MA_COLORS[ma], width=1.5, dash="dot")))
        st.plotly_chart(base_layout(fig, 480, t("price_axis")), width="stretch")

        s = ind.snapshot(df)
        m = st.columns(6)
        m[0].metric(t("vs_ma50"), fmt_pct(s["dev_ma50_pct"]), help=f"MA50 = {s['ma50']:.2f}")
        m[1].metric(t("vs_ma200"), fmt_pct(s["dev_ma200_pct"]), help=f"MA200 = {s['ma200']:.2f}")
        m[2].metric(t("dd_ath"), fmt_pct(s["drawdown_pct"]), help=f"ATH = {s['ath']:.2f}")
        m[3].metric(t("max_dd"), fmt_pct(s["max_drawdown_pct"]),
                    help=t("trough_on", d=s["max_drawdown_date"]))
        m[4].metric(t("vol_20_1y"), f"{s['vol_20d']:.1f}% / {s['vol_1y']:.1f}%", help=t("vol_help"))
        regime = t("golden") if s["ma50_above_ma200"] else t("death")
        last_typ = t(s["last_cross_type"].lower()) if s["last_cross_type"] else "-"
        m[5].metric(t("trend"), regime,
                    help=t("trend_help", rel=">" if s["ma50_above_ma200"] else "<",
                           typ=last_typ, d=s["last_cross_date"]))
        r = st.columns(5)
        for col, (label, val) in zip(r, s["returns"].items()):
            col.metric(t("return_p", p=label), fmt_pct(val))

# --------------------------------------------------------------------------- #
# 3. Drawdown chart
# --------------------------------------------------------------------------- #
with tabs[1]:
    st.subheader(t("dd_title"))
    st.caption(t("dd_caption"))
    fig = go.Figure()
    for sym in SYMBOLS:
        df = live_frame(sym)
        if df is None:
            st.warning(t("sym_unavailable", sym=sym))
            continue
        dd = ind.drawdown_series(df["Close"])
        fig.add_trace(go.Scatter(x=dd.index, y=dd, name=sym, line=dict(color=COLORS[sym], width=1.5),
                                 hovertemplate="%{y:.2f}%"))
    fig.add_hline(y=-10, line=dict(color="gray", dash="dash", width=1), annotation_text=t("correction"))
    fig.add_hline(y=-20, line=dict(color="gray", dash="dash", width=1), annotation_text=t("bear"))
    st.plotly_chart(base_layout(fig, 450, t("dd_axis")), width="stretch")

# --------------------------------------------------------------------------- #
# 4. SPY vs QQQ comparison
# --------------------------------------------------------------------------- #
with tabs[2]:
    rng = st.radio(t("range"), list(RANGES), index=3, horizontal=True, key="cmp_rng")
    frames = {s: live_frame(s) for s in SYMBOLS}
    if any(f is None for f in frames.values()):
        st.error(t("cmp_unavailable"))
    else:
        st.subheader(t("norm_title"))
        fig = go.Figure()
        for sym, df in frames.items():
            c = df["Close"].loc[df.index[-1] - RANGES[rng]:]
            fig.add_trace(go.Scatter(x=c.index, y=c / c.iloc[0] * 100, name=sym,
                                     line=dict(color=COLORS[sym], width=2),
                                     hovertemplate="%{y:.1f}"))
        st.plotly_chart(base_layout(fig, 420, t("growth_axis")), width="stretch")

        st.subheader(t("risk_title"))
        rows = {}
        for sym, df in frames.items():
            s = ind.snapshot(df)
            rows[sym] = {
                t("vol20_ann"): f"{s['vol_20d']:.1f}%",
                t("vol1y_ann"): f"{s['vol_1y']:.1f}%",
                t("vol10y_ann"): f"{ind.annualized_vol(df['Close'], len(df)):.1f}%",
                t("cur_dd"): fmt_pct(s["drawdown_pct"]),
                t("max_dd"): fmt_pct(s["max_drawdown_pct"]),
                **{t("return_p", p=k): fmt_pct(v) for k, v in s["returns"].items()},
            }
        st.dataframe(pd.DataFrame(rows), width="stretch")

        st.subheader(t("rollvol_title"))
        fig = go.Figure()
        for sym, df in frames.items():
            v = ind.rolling_vol(df["Close"]).loc[df.index[-1] - RANGES[rng]:]
            fig.add_trace(go.Scatter(x=v.index, y=v, name=sym, line=dict(color=COLORS[sym], width=1.5),
                                     hovertemplate="%{y:.1f}%"))
        st.plotly_chart(base_layout(fig, 350, t("vol_axis")), width="stretch")

# --------------------------------------------------------------------------- #
# 5. Declines & recoveries
# --------------------------------------------------------------------------- #
with tabs[3]:
    st.subheader(t("ev_title"))
    st.caption(t("ev_caption"))
    for sym in SYMBOLS:
        df = live_frame(sym)
        if df is None:
            st.warning(t("sym_unavailable", sym=sym))
            continue
        st.markdown(f"#### {sym}")
        for th in (10, 20):
            ev = ind.drawdown_events(df["Close"], th)
            st.markdown(t("ev_header", th=th, n=len(ev)))
            if ev.empty:
                st.info(t("ev_none"))
            else:
                shown = ev.astype(str).replace("Not recovered", t("Not recovered"))
                shown.columns = [t(c) for c in shown.columns]
                st.dataframe(shown, hide_index=True, width="stretch")

# --------------------------------------------------------------------------- #
# 6. Alert rules editor + notification settings
# --------------------------------------------------------------------------- #
with tabs[4]:
    cfg = rules.load_config()
    st.subheader(t("rules_title"))
    st.caption(t("rules_caption"))

    # Rule-type dropdown shows localised labels; map them back to type keys on save.
    label_to_type = {rule_label(rt): rt for rt in rules.RULE_TYPES}
    table = pd.DataFrame([{
        "id": r["id"], "enabled": bool(r["enabled"]), "symbol": r["symbol"],
        "rule": rule_label(r["type"]), "value": r.get("value"), "note": r.get("note", ""),
    } for r in cfg["rules"]], columns=["id", "enabled", "symbol", "rule", "value", "note"])

    edited = st.data_editor(
        table, num_rows="dynamic", hide_index=True, width="stretch",
        key=f"rules_editor_{lang()}",  # separate editor state per language
        column_config={
            "id": None,  # hidden
            "enabled": st.column_config.CheckboxColumn(t("col_enabled"), default=True),
            "symbol": st.column_config.SelectboxColumn(t("symbol"), options=SYMBOLS, required=True,
                                                       default="SPY"),
            "rule": st.column_config.SelectboxColumn(t("col_rule"), options=list(label_to_type),
                                                     required=True, width="large"),
            "value": st.column_config.NumberColumn(t("col_value"), min_value=0.0, format="%.2f"),
            "note": st.column_config.TextColumn(t("col_note")),
        })

    if st.button(t("save_rules"), type="primary"):
        new_rules, problems = [], []
        for i, row in edited.iterrows():
            if pd.isna(row["rule"]) or pd.isna(row["symbol"]):
                problems.append(t("err_required", i=i + 1))
                continue
            rtype = label_to_type[row["rule"]]
            needs_value = rules.RULE_TYPES[rtype][1]
            value = None if pd.isna(row["value"]) else float(row["value"])
            if needs_value and value is None:
                problems.append(t("err_value", i=i + 1, rule=row["rule"]))
                continue
            new_rules.append({
                "id": row["id"] if isinstance(row["id"], str) and row["id"] else rules.new_id(),
                "symbol": row["symbol"], "type": rtype,
                "value": value if needs_value else None,
                "enabled": bool(row["enabled"]) if not pd.isna(row["enabled"]) else True,
                "note": "" if pd.isna(row["note"]) else str(row["note"]),
            })
        if problems:
            st.error(t("not_saved") + "\n\n" + "\n\n".join(problems))
        else:
            cfg["rules"] = new_rules
            rules.save_config(cfg)
            st.success(t("saved_rules", n=len(new_rules)))

    st.subheader(t("live_status"))
    snaps = {}
    for sym in SYMBOLS:
        df = live_frame(sym)
        if df is not None:
            snaps[sym] = ind.snapshot(df)
    status = [{t("st_enabled"): "✅" if r["enabled"] else "⏸",
               t("st_rule"): describe_rule(r),
               t("st_met"): (t("yes") if rules.evaluate(r, snaps[r["symbol"]]) else t("no"))
               if r["symbol"] in snaps else t("data_unavailable"),
               t("st_note"): r.get("note", "")} for r in cfg["rules"]]
    st.dataframe(pd.DataFrame(status), hide_index=True, width="stretch")
    if st.button(t("check_now")):
        fired = rules.check_and_notify(snaps, cfg)
        st.success(t("fired_n", n=len(fired)) if fired else t("fired_none"))

    st.subheader(t("notif_title"))
    s = cfg["settings"]
    with st.form("settings"):
        topic = st.text_input(t("ntfy_topic"), s["ntfy_topic"], help=t("ntfy_help"))
        interval = st.number_input(t("interval"), 1, 120, int(s["check_interval_min"]))
        desktop = st.checkbox(t("desktop"), s["desktop_notify"])
        if st.form_submit_button(t("save_settings")):
            cfg["settings"] = {"ntfy_topic": topic.strip(), "check_interval_min": int(interval),
                               "desktop_notify": desktop}
            rules.save_config(cfg)
            st.success(t("settings_saved"))
    if st.button(t("test_notif")):
        ok_d = notify.desktop("Test alert", "SPY/QQQ Monitor notifications are working.")
        ok_n = notify.ntfy(cfg["settings"]["ntfy_topic"], "Test alert",
                           "SPY/QQQ Monitor notifications are working.")
        if not cfg["settings"]["ntfy_topic"]:
            ntfy_status = t("not_configured")
        else:
            ntfy_status = t("sent") if ok_n else t("ntfy_failed")
        st.info(t("test_result", d=t("sent") if ok_d else t("failed"), n=ntfy_status))

# --------------------------------------------------------------------------- #
# 7. Alert log
# --------------------------------------------------------------------------- #
with tabs[5]:
    st.subheader(t("log_title"))
    log_df = rules.read_log()
    if log_df.empty:
        st.info(t("log_empty"))
    else:
        log_df = log_df.sort_values("timestamp_et", ascending=False).drop(columns=["rule_id"])
        st.dataframe(log_df.head(200), hide_index=True, width="stretch", column_config={
            "timestamp_et": t("log_time"), "symbol": t("symbol"), "rule": t("st_rule"),
            "price": st.column_config.NumberColumn(t("log_price"), format="$%.2f"),
            "change_pct": st.column_config.NumberColumn(t("log_chg"), format="%+.2f%%"),
            "dev_ma200_pct": st.column_config.NumberColumn(t("vs_ma200"), format="%+.2f%%"),
            "drawdown_pct": st.column_config.NumberColumn(t("log_dd"), format="%.2f%%"),
            "vol_20d": st.column_config.NumberColumn(t("log_vol"), format="%.1f%%"),
        })
        if lang() == "zh":
            st.caption(t("log_note"))
        st.download_button(t("download_csv"), log_df.to_csv(index=False), "alerts_log.csv")

st.divider()
st.caption(t("disclaimer"))
