"""Step 5a: report.html (Plotly, single self-contained file)."""
from __future__ import annotations

import html
import json
import logging

import numpy as np
import pandas as pd
import plotly.graph_objects as go

from . import timeutil as tu

log = logging.getLogger("events.report")

# Categorical slots (validated reference palette), assigned to issuers in a FIXED order so an issuer keeps
# its colour in every event. Venues of the same issuer are told apart by dash style.
ISSUER_COLOR = {"ondo": "#2a78d6", "xstocks": "#eb6834", "bstocks": "#1baf7a", "robinhood": "#eda100",
                "dinari": "#e87ba4", "native": "#008300", "perp": "#4a3aa7"}
REF_STYLE = {"stock": dict(color="#0b0b0b", width=2.5, dash="solid"),
             "ref": dict(color="#7a7974", width=2, dash="dot"),
             "perp_index": dict(color="#b5b4ae", width=1.2, dash="dot"),
             "perp_mark": dict(color="#b5b4ae", width=1.2, dash="dash")}
DASHES = ["solid", "dash", "dot", "dashdot", "longdash", "longdashdot"]
SESSION_FILL = {"closed": "rgba(82,81,78,0.10)", "pre": "rgba(82,81,78,0.05)", "post": "rgba(82,81,78,0.05)"}
INK, INK2, GRID = "#0b0b0b", "#52514e", "#e7e6e2"
DIVERGING = [[0, "#1c5cab"], [0.5, "#f0efec"], [1, "#c23b3b"]]

NOTES = """
<h2>Lưu ý khi diễn giải</h2>
<ul>
<li>Giá nến là <b>giá khớp cuối</b> trong nến. Nến volume 0 không phải giá giao dịch được: bị loại khỏi median, dispersion,
premium và arb window. Đường giá trên chart là giá khớp gần nhất (giữ nguyên qua các nến không khớp).</li>
<li>"Giá tại thời điểm t" = giá khớp cuối của nến đã <b>kết thúc</b> trước hoặc đúng t (nến mở ≤ t − 5 phút).
Vì vậy P(09:30 ET) là giá ngay trước giờ mở cửa, chưa gồm phiên mở cửa.</li>
<li>Mọi giá token là <b>P_adj = P / k</b>, k = median(P_token / P_stock) trong phiên chính của ngày giao dịch trước event
(chỉ nến có volume &gt; 0). USDT/USDC được quy đổi sang USD khi peg lệch &gt; ngưỡng.</li>
<li>Token của các issuer khác nhau <b>không chuyển đổi trực tiếp</b> cho nhau. Arb window chỉ là chênh lệch giá; còn phải
tính rủi ro issuer, bridge/rút nạp, phí, spread và độ sâu sổ lệnh.</li>
<li>Giá mở cửa chính thức (opening cross) có thể khác giá khớp 5 phút đầu phiên.</li>
<li>Mẫu 5–6 event chỉ để minh hoạ, <b>không đủ</b> để kết luận thống kê.</li>
<li>captured(t) = (P_adj(t) − C0) / (O1 − C0). t50/t90: lần đầu captured ≥ 50%/90% và giữ ít nhất 30 phút
(tính từ t_evt tới 09:30 ET). max_overshoot: vượt quá O1 theo chiều gap (% so với O1); max_wrong_way: đi ngược chiều gap
so với C0 (% so với C0). Lead-lag: tương quan chéo lợi suất log 5m, lag dương = A dẫn B.</li>
</ul>"""

CSS = """
:root{--surface:#ffffff;--ink:#0b0b0b;--ink2:#52514e;--rule:#e7e6e2;--head:#6b4226}
body{background:var(--surface);color:var(--ink);font:14px/1.5 -apple-system,Segoe UI,Roboto,Helvetica,Arial,sans-serif;
margin:0 auto;max-width:1280px;padding:16px}
h1{font-size:24px;margin:8px 0}h2{font-size:19px;margin:28px 0 8px;border-bottom:2px solid var(--rule);padding-bottom:4px}
h3{font-size:15px;margin:18px 0 6px;color:var(--ink2)}
table{border-collapse:collapse;font-size:12.5px;margin:6px 0 14px;display:block;overflow-x:auto;max-width:100%}
th{background:var(--head);color:#fff;font-weight:700;padding:5px 8px;text-align:left;white-space:nowrap;position:sticky;top:0}
td{padding:4px 8px;border-bottom:1px solid var(--rule);white-space:nowrap;font-variant-numeric:tabular-nums}
td.num{text-align:right}.warn{background:#fff6e0;border-left:4px solid #eda100;padding:6px 10px;margin:6px 0}
.meta{color:var(--ink2)}.toc a{margin-right:14px}section.event{margin-top:30px}
"""


def _style_for(label: str, kind: str, issuer: str, seen: dict) -> dict:
    if kind in REF_STYLE:
        return REF_STYLE[kind]
    base = "native" if issuer.startswith("native") else issuer
    color = ISSUER_COLOR.get(base, "#4a3aa7")
    n = seen.setdefault(base, 0)
    seen[base] = n + 1
    return dict(color=color, width=1.8 if kind != "perp" else 1.6, dash=DASHES[n % len(DASHES)])


def _session_bands(fig, idx: pd.DatetimeIndex, row=None):
    if len(idx) == 0:
        return
    lab = pd.Series([tu.us_session_label(t) for t in idx], index=idx)
    grp = (lab != lab.shift()).cumsum()
    for _, seg in lab.groupby(grp):
        kind = seg.iloc[0]
        if kind == "regular":
            continue
        x0 = tu.to_et_naive(pd.DatetimeIndex([seg.index[0]]))[0]
        x1 = tu.to_et_naive(pd.DatetimeIndex([seg.index[-1] + tu.BAR]))[0]
        fig.add_vrect(x0=x0, x1=x1, fillcolor=SESSION_FILL[kind], line_width=0, layer="below",
                      annotation_text={"closed": "đóng cửa", "pre": "pre-market", "post": "after-hours"}[kind],
                      annotation_position="top left", annotation_font_size=10, annotation_font_color=INK2)


def _vline(fig, ts, text, dash="dash"):
    x = tu.to_et_naive(pd.DatetimeIndex([pd.Timestamp(ts)]))[0]
    fig.add_vline(x=x, line_width=1.2, line_dash=dash, line_color=INK2)
    fig.add_annotation(x=x, y=1.0, yref="paper", text=text, showarrow=False, yanchor="bottom",
                       font=dict(size=10, color=INK2), bgcolor="rgba(255,255,255,0.8)")


def _layout(fig, title, ytitle, height=520):
    fig.update_layout(title=dict(text=title, font=dict(size=15, color=INK)), height=height, template="plotly_white",
                      paper_bgcolor="#ffffff", plot_bgcolor="#ffffff", hovermode="x unified",
                      margin=dict(l=60, r=20, t=70, b=50), legend=dict(orientation="h", y=-0.15, font=dict(size=11)),
                      font=dict(color=INK))
    fig.update_xaxes(title="giờ New York (ET)", gridcolor=GRID, showspikes=True, spikemode="across",
                     spikethickness=1, spikecolor=INK2)
    fig.update_yaxes(title=ytitle, gridcolor=GRID, zerolinecolor="#b5b4ae")
    return fig


def _hover_cols(idx):
    et = idx.tz_convert(tu.ET).strftime("%m-%d %H:%M ET")
    vn = idx.tz_convert(tu.VN).strftime("%m-%d %H:%M VN")
    return et, vn


def fig_prices(d: dict) -> go.Figure:
    ev, adj, traded, volq = d["ev"], d["adj"], d["traded"], d["volq"]
    c0, o1 = ev["c0"], ev["o1"]
    m = (adj.index >= pd.Timestamp(ev["win_start"])) & (adj.index < pd.Timestamp(ev["win_end"]))
    a, tr, vq = adj.loc[m], traded.loc[m], volq.loc[m]
    x = tu.to_et_naive(a.index)
    et, vn = _hover_cols(a.index)
    fig = go.Figure()
    seen = {}
    order = sorted(a.columns, key=lambda s: ({"stock": 0, "ref": 1, "perp": 3, "perp_index": 4, "perp_mark": 5}
                                           .get(d["kinds"][s], 2), d["labels"][s]))
    for s in order:
        kind, label = d["kinds"][s], d["labels"][s]
        issuer = label.split("@")[0]
        y = (a[s] / c0 - 1) * 100
        if y.notna().sum() == 0:
            continue
        vol = vq[s].fillna(0).round(0) if s in vq else pd.Series(0, index=a.index)
        custom = np.stack([et, vn, vol.map(lambda v: f"{v:,.0f}"),
                           np.where(tr[s], "khớp", "không khớp")], axis=-1)
        fig.add_trace(go.Scatter(
            x=x, y=y, name=label, mode="lines", line=_style_for(label, kind, issuer, seen), line_shape="hv",
            customdata=custom, connectgaps=False,
            hovertemplate=f"<b>{html.escape(label)}</b> %{{y:+.2f}}%  vol $%{{customdata[2]}} (%{{customdata[3]}})"
                          "<br>%{customdata[0]} · %{customdata[1]}<extra></extra>"))
    gap = (o1 / c0 - 1) * 100
    fig.add_hline(y=gap, line_color=INK, line_width=1, line_dash="dot",
                  annotation_text=f"O1 = {o1:,.2f} ({gap:+.2f}%)", annotation_position="top left",
                  annotation_font_size=11)
    fig.add_hline(y=0, line_color="#b5b4ae", line_width=1, annotation_text=f"C0 = {c0:,.2f}",
                  annotation_position="top right", annotation_font_size=11)
    _session_bands(fig, a.index)
    _vline(fig, ev["win_start"], "t_evt − 12h")
    _vline(fig, ev["t_evt"], "event")
    _vline(fig, ev["open1"], "09:30 ET", dash="solid")
    return _layout(fig, f"{ev['id']}: P_adj so với C0 (%)", "% so với C0", 560)


def fig_dispersion(d: dict, thr: float) -> go.Figure:
    xs, arb, ev = d["xs"], d["arb"], d["ev"]
    fig = go.Figure()
    if xs.empty or xs["dispersion"].notna().sum() == 0:
        fig.add_annotation(text="Chưa đủ ≥ 2 nguồn token có khớp lệnh cùng nến", showarrow=False, x=0.5, y=0.5,
                           xref="paper", yref="paper")
        return _layout(fig, f"{ev['id']}: dispersion giữa các issuer", "%", 300)
    x = tu.to_et_naive(xs.index)
    et, vn = _hover_cols(xs.index)
    lab = d["labels"]
    custom = np.stack([et, vn, xs["rich"].map(lambda s: lab.get(s, "")), xs["cheap"].map(lambda s: lab.get(s, "")),
                       xs["n_live"].astype(int)], axis=-1)
    fig.add_trace(go.Scatter(x=x, y=xs["dispersion"] * 100, mode="lines", name="dispersion",
                             line=dict(color="#2a78d6", width=2), customdata=custom, connectgaps=False,
                             hovertemplate="dispersion %{y:.2f}% · %{customdata[4]} nguồn khớp<br>đắt: %{customdata[2]}"
                                           " · rẻ: %{customdata[3]}<br>%{customdata[0]} · %{customdata[1]}<extra></extra>"))
    fig.add_hline(y=thr * 100, line_dash="dash", line_color="#c98500",
                  annotation_text=f"ngưỡng chi phí {thr:.2%}", annotation_position="top left", annotation_font_size=11)
    for _, w in arb.iterrows():
        x0 = tu.to_et_naive(pd.DatetimeIndex([pd.Timestamp(w["start"])]))[0]
        x1 = tu.to_et_naive(pd.DatetimeIndex([pd.Timestamp(w["end"])]))[0]
        fig.add_vrect(x0=x0, x1=x1, fillcolor="rgba(237,161,0,0.28)", line_width=0, layer="below")
    _vline(fig, ev["t_evt"], "event")
    _vline(fig, ev["open1"], "09:30 ET", dash="solid")
    fig = _layout(fig, f"{ev['id']}: dispersion = (max − min) / median, chỉ nguồn có khớp; vùng vàng = arb window",
                  "dispersion (%)", 320)
    fig.update_layout(showlegend=False)
    return fig


def fig_premium_heatmap(d: dict) -> go.Figure:
    prem, ev, lab = d["prem"], d["ev"], d["labels"]
    fig = go.Figure()
    if prem.empty:
        return _layout(fig, f"{ev['id']}: premium_i", "", 250)
    z = prem.T * 100
    lim = float(np.nanpercentile(np.abs(z.values), 98)) if np.isfinite(z.values).any() else 1.0
    lim = max(lim, 0.1)
    x = tu.to_et_naive(prem.index)
    et, vn = _hover_cols(prem.index)
    fig.add_trace(go.Heatmap(z=z.values, x=x, y=[lab[s] for s in prem.columns], zmid=0, zmin=-lim, zmax=lim,
                             colorscale=DIVERGING, colorbar=dict(title="%", thickness=12),
                             customdata=np.tile(np.array(list(zip(et, vn))), (len(prem.columns), 1, 1)),
                             hovertemplate="%{y}: %{z:+.2f}% vs median<br>%{customdata[0]} · %{customdata[1]}"
                                           "<extra></extra>", hoverongaps=False))
    _vline(fig, ev["t_evt"], "event")
    _vline(fig, ev["open1"], "09:30 ET", dash="solid")
    fig = _layout(fig, f"{ev['id']}: premium_i = P_adj_i / median − 1 (ô trống = không khớp lệnh)", "",
                  120 + 34 * len(prem.columns))
    fig.update_layout(hovermode="closest")
    return fig


def _fmt(v, pct=False, dec=2):
    if v is None or (isinstance(v, float) and not np.isfinite(v)):
        return "–"
    if isinstance(v, (int, float, np.floating)):
        return f"{v * 100:+.{dec}f}%" if pct else f"{v:,.{dec}f}"
    return html.escape(str(v))


def html_table(df: pd.DataFrame, pct_cols=(), dec_cols=None) -> str:
    dec_cols = dec_cols or {}
    head = "".join(f"<th>{html.escape(str(c))}</th>" for c in df.columns)
    body = []
    for _, r in df.iterrows():
        cells = []
        for c in df.columns:
            v = r[c]
            num = isinstance(v, (int, float, np.floating)) and not isinstance(v, bool)
            txt = _fmt(v, c in pct_cols, dec_cols.get(c, 2)) if num else html.escape("" if pd.isna(v) else str(v))
            cells.append(f"<td class='{'num' if num else ''}'>{txt}</td>")
        body.append("<tr>" + "".join(cells) + "</tr>")
    return f"<table><thead><tr>{head}</tr></thead><tbody>{''.join(body)}</tbody></table>"


RANK_COLS = ["label", "kind", "interval", "t50", "t50_min_after_event", "t90", "t90_min_after_event",
             "residual_preopen", "residual_at_open", "move_token", "captured_t+1h", "captured_03:00ET",
             "captured_09:25ET", "max_overshoot", "max_wrong_way", "pct_zero_volume_bars", "volume_usd",
             "stale_min_at_0925", "premium_vs_pyth_mean_night"]
PCT = {"residual_preopen", "residual_at_open", "move_token", "captured_t+1h", "captured_03:00ET", "captured_09:25ET",
       "max_overshoot", "max_wrong_way", "pct_zero_volume_bars", "premium_vs_pyth_mean_night", "k_minus_1",
       "max_dispersion", "best_corr", "corr_lag0", "residual_preopen_mean", "dispersion_max"}


def load_event(paths, eid) -> dict | None:
    p = paths.analysis / eid
    if not (p / "event.json").exists():
        return None
    ev = json.loads((p / "event.json").read_text())
    rd = lambda n: pd.read_parquet(p / f"{n}.parquet")  # noqa: E731
    csv = lambda n: pd.read_csv(p / f"{n}.csv") if (p / f"{n}.csv").stat().st_size > 1 else pd.DataFrame()  # noqa
    d = {"ev": ev, "adj": rd("adj"), "traded": rd("traded").astype(bool), "volq": rd("volq"), "xs": rd("xs"),
         "prem": rd("prem"), "metrics": csv("metrics"), "arb": csv("arb"), "k": csv("k"), "leadlag": csv("leadlag"),
         "labels": ev["labels"], "kinds": ev["kinds"]}
    d["funding"] = pd.read_parquet(p / "funding.parquet") if (p / "funding.parquet").exists() else pd.DataFrame()
    return d


def _event_section(d, thr, first_js) -> tuple[str, bool]:
    ev = d["ev"]
    parts = [f"<section class='event' id='{ev['id']}'><h2>{html.escape(ev['id'])}</h2>",
             f"<p class='meta'>{ev['ticker']} · nhóm vốn hoá <b>{ev['cap_group']}</b> · {ev['event_type']} · "
             f"event {ev['t_event_et']} = {tu.fmt_utc(ev['t_evt'])} = {ev['t_event_vn']}<br>"
             f"C0 ({ev['prev_session']}) = {ev['c0']:,.2f} → O1 ({ev['next_session']}) = {ev['o1']:,.2f} · "
             f"gap <b>{ev['gap'] * 100:+.2f}%</b> · cửa sổ {tu.fmt_et(ev['win_start'])} → {tu.fmt_et(ev['win_end'])}"
             f" · k tính theo {html.escape(ev.get('calibration_ref') or '–')}</p>"]
    if ev.get("note"):
        parts.append(f"<p class='meta'>Ghi chú: {html.escape(ev['note'])}</p>")
    for w in ev.get("warnings", []):
        parts.append(f"<div class='warn'>⚠ {html.escape(w)}</div>")
    for f in (fig_prices(d), fig_dispersion(d, thr), fig_premium_heatmap(d)):
        parts.append(f.to_html(full_html=False, include_plotlyjs=first_js, config={"displaylogo": False}))
        first_js = False
    met = d["metrics"]
    if not met.empty:
        tok = met[met["kind"].isin(["cex_spot", "dex"])].sort_values(["t50_min_after_event", "t90_min_after_event"])
        oth = met[~met["kind"].isin(["cex_spot", "dex"])]
        parts.append("<h3>Xếp hạng issuer dẫn giá (token, theo t50 rồi t90) + đối chứng</h3>")
        cols = [c for c in RANK_COLS if c in met.columns]
        parts.append(html_table(pd.concat([tok, oth])[cols], PCT, {"t50_min_after_event": 0,
                                                                   "t90_min_after_event": 0, "volume_usd": 0,
                                                                   "stale_min_at_0925": 0}))
    if not d["arb"].empty:
        parts.append("<h3>Arb windows</h3>")
        a = d["arb"].copy()
        for c in ("start", "end", "peak_at"):
            a[c] = a[c].map(tu.fmt_et)
        parts.append(html_table(a.drop(columns=["event_id"], errors="ignore"), PCT, {"duration_min": 0, "bars": 0}))
    else:
        parts.append(f"<p class='meta'>Không có arb window nào vượt ngưỡng {thr:.2%}.</p>")
    if not d["k"].empty:
        parts.append("<h3>Hệ số hiệu chỉnh k</h3>")
        kk = d["k"][["source", "kind", "quote", "interval", "k", "k_std", "k_n", "k_minus_1", "warn", "method", "fx"]]
        parts.append(html_table(kk, PCT, {"k": 5, "k_std": 5, "k_n": 0}))
    if not d["leadlag"].empty:
        parts.append("<h3>Lead-lag (tương quan chéo lợi suất 5m, từ t_evt)</h3>")
        parts.append(html_table(d["leadlag"][["a", "b", "best_lag_bars", "best_corr", "corr_lag0"]], set(),
                                {"best_lag_bars": 0, "best_corr": 3, "corr_lag0": 3}))
    if not d["funding"].empty:
        f = d["funding"].copy()
        f["ts"] = f["ts"].map(tu.fmt_et)
        parts.append("<h3>Funding (Binance perp)</h3>" + html_table(f, {"funding_rate"}, {"mark_price": 2}))
    parts.append("</section>")
    return "\n".join(parts), first_js


def _bar(df, x, y, title, ytitle, pct=True, first_js=False):
    fig = go.Figure(go.Bar(x=df[x], y=df[y] * (100 if pct else 1), marker_color="#2a78d6",
                           hovertemplate="%{x}: %{y:.2f}" + ("%" if pct else "") + "<extra></extra>"))
    fig = _layout(fig, title, ytitle, 340)
    fig.update_layout(hovermode="closest", showlegend=False, bargap=0.55)
    fig.update_xaxes(title="")
    return fig.to_html(full_html=False, include_plotlyjs=first_js, config={"displaylogo": False})


def summary(all_d: list[dict]) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    met = pd.concat([d["metrics"] for d in all_d if not d["metrics"].empty], ignore_index=True) \
        if any(not d["metrics"].empty for d in all_d) else pd.DataFrame()
    ev_rows = []
    for d in all_d:
        ev = d["ev"]
        xs = d["xs"]
        ev_rows.append({"event_id": ev["id"], "cap_group": ev["cap_group"], "gap": ev["gap"],
                        "n_arb_windows": len(d["arb"]),
                        "arb_minutes": float(d["arb"]["duration_min"].sum()) if not d["arb"].empty else 0.0,
                        "dispersion_max": float(xs["dispersion"].max()) if "dispersion" in xs else np.nan})
    evs = pd.DataFrame(ev_rows)
    by_issuer = pd.DataFrame()
    if not met.empty:
        tok = met[met["kind"].isin(["cex_spot", "dex", "perp"])]
        by_issuer = tok.groupby("issuer").agg(
            n_sources=("source", "count"), residual_preopen_mean=("residual_preopen", "mean"),
            abs_residual_preopen_mean=("residual_preopen", lambda s: s.abs().mean()),
            t50_min_median=("t50_min_after_event", "median"), t90_min_median=("t90_min_after_event", "median"),
            pct_zero_volume_bars=("pct_zero_volume_bars", "mean"), volume_usd=("volume_usd", "sum")).reset_index()
    return met, evs, by_issuer


def build(paths, cfg, event_ids: list[str]) -> str:
    all_d = [d for d in (load_event(paths, e) for e in event_ids) if d]
    if not all_d:
        raise SystemExit("Nothing analyzed yet: run `python run.py analyze` first.")
    thr = cfg["arb_threshold"]
    toc = " ".join(f"<a href='#{d['ev']['id']}'>{d['ev']['id']}</a>" for d in all_d)
    body = [f"<h1>Token cổ phiếu đa issuer qua event ban đêm</h1><p class='meta'>Tạo lúc "
            f"{pd.Timestamp.now(tz=tu.VN):%Y-%m-%d %H:%M} VN · {len(all_d)} event · nến 5 phút · "
            f"ngưỡng arb {thr:.2%}</p>", NOTES, f"<p class='toc'><b>Event:</b> {toc} <a href='#summary'>Tổng hợp</a></p>"]
    first_js = True
    for d in all_d:
        sec, first_js = _event_section(d, thr, first_js)
        body.append(sec)
    met, evs, by_issuer = summary(all_d)
    body.append("<section id='summary'><h2>Tổng hợp</h2>")
    if not by_issuer.empty:
        body.append(_bar(by_issuer, "issuer", "residual_preopen_mean",
                         "residual_preopen trung bình theo issuer (P_adj 09:25 ET / O1 − 1)", "%", True, first_js))
        first_js = False
        body.append(html_table(by_issuer, PCT | {"abs_residual_preopen_mean"},
                               {"n_sources": 0, "t50_min_median": 0, "t90_min_median": 0, "volume_usd": 0}))
    if not met.empty:
        cg = met[met["kind"].isin(["cex_spot", "dex"])].groupby("cap_group")["residual_preopen"] \
            .agg(lambda s: s.abs().mean()).reset_index()
        body.append(_bar(cg, "cap_group", "residual_preopen", "|residual_preopen| trung bình theo nhóm vốn hoá "
                         "(nguồn token)", "%", True, first_js))
        first_js = False
    if not evs.empty:
        body.append(_bar(evs, "event_id", "n_arb_windows", "Số arb window theo event", "số window", False, first_js))
        body.append(_bar(evs, "event_id", "dispersion_max", "Dispersion max theo event", "%", True, False))
        body.append(html_table(evs, PCT | {"gap"}, {"n_arb_windows": 0, "arb_minutes": 0}))
    body.append("</section>")
    doc = (f"<!doctype html><html lang='vi'><head><meta charset='utf-8'><meta name='viewport' "
           f"content='width=device-width,initial-scale=1'><title>Token Event Study</title><style>{CSS}</style>"
           f"</head><body>{''.join(body)}</body></html>")
    paths.report.write_text(doc, encoding="utf-8")
    return str(paths.report)
