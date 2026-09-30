import sys
from datetime import date
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from events import metrics as M  # noqa: E402
from events import timeutil as tu  # noqa: E402
from events.discover import _match_suffix, classify_night  # noqa: E402
from events.normalize import calibrate_k, convert_usd, to_grid  # noqa: E402

T0 = pd.Timestamp("2026-09-10 13:30", tz="UTC")  # 09:30 ET (EDT)


def idx(n, start=T0):
    return pd.date_range(start, periods=n, freq="5min", tz="UTC")


# ---------------------------------------------------------------- k calibration
def test_k_is_median_ratio_on_traded_bars_only():
    ix = idx(78)
    stock = pd.Series(100.0 + np.arange(78) * 0.1, index=ix)
    token = stock * 1.0123
    traded = pd.Series(True, index=ix)
    token.iloc[5] = 999.0            # garbage print on a zero-volume bar must be ignored
    traded.iloc[5] = False
    k = calibrate_k(token, traded, stock, ix[0], ix[-1] + tu.BAR)
    assert k["k"] == pytest.approx(1.0123)
    assert k["k_std"] == pytest.approx(0, abs=1e-12)
    assert k["k_n"] == 77


def test_k_only_uses_the_session_window():
    ix = idx(100)
    stock = pd.Series(100.0, index=ix)
    token = pd.Series(101.0, index=ix)
    token.iloc[:10] = 150.0          # before the session
    k = calibrate_k(token, pd.Series(True, index=ix), stock, ix[10], ix[-1] + tu.BAR)
    assert k["k"] == pytest.approx(1.01)


def test_k_nan_without_traded_bars():
    ix = idx(10)
    k = calibrate_k(pd.Series(1.0, index=ix), pd.Series(False, index=ix), pd.Series(1.0, index=ix), ix[0], ix[-1])
    assert np.isnan(k["k"]) and k["k_n"] == 0


# ---------------------------------------------------------------- captured / t50 / overshoot
def test_captured_values():
    assert M.captured(103.75, 100, 107.5) == pytest.approx(0.5)
    assert M.captured(107.5, 100, 107.5) == pytest.approx(1.0)
    assert M.captured(95.0, 100, 90.0) == pytest.approx(0.5)      # negative gap
    assert np.isnan(M.captured(101.0, 100, 100))                  # no gap -> undefined


def test_first_hold_time_requires_holding():
    ix = idx(20)
    cap = pd.Series(0.0, index=ix)
    cap.iloc[2] = 0.6                  # one-bar spike, not held
    cap.iloc[8:] = 0.7                 # reached at bar 8 and held
    t = M.first_hold_time(cap, 0.5, pd.Timedelta(minutes=30))
    assert t == ix[8] + tu.BAR
    assert M.first_hold_time(cap, 0.9, pd.Timedelta(minutes=30)) is None


def test_price_at_uses_completed_bars():
    ix = idx(4)
    p = pd.Series([1.0, 2.0, 3.0, 4.0], index=ix)
    assert M.price_at(p, ix[2]) == 2.0      # bar ix[2] has not finished at ix[2]
    assert M.price_at(p, ix[2] + tu.BAR) == 3.0


def test_overshoot_and_wrong_way():
    p = pd.Series([99.0, 104.0, 109.0, 107.0])
    over, wrong = M.overshoot_wrongway(p, 100.0, 107.5)
    assert over == pytest.approx(109 / 107.5 - 1)
    assert wrong == pytest.approx(0.01)


# ---------------------------------------------------------------- dispersion / premium / arb windows
def _panel():
    ix = idx(6)
    prices = pd.DataFrame({"a": [100, 100, 100, 100, 100, 100.0],
                           "b": [100, 101, 101, 100, 100, 100.0],
                           "c": [100, 99, 99.2, 100, 50, 100.0]}, index=ix)
    traded = pd.DataFrame(True, index=ix, columns=prices.columns)
    traded.loc[ix[4], "c"] = False      # the 50 print has no volume -> must be ignored
    return prices, traded


def test_dispersion_ignores_zero_volume_bars():
    prices, traded = _panel()
    xs = M.cross_section(prices, traded)
    assert xs["dispersion"].iloc[1] == pytest.approx((101 - 99) / 100)
    assert xs["dispersion"].iloc[4] == pytest.approx(0.0)
    assert xs["rich"].iloc[1] == "b" and xs["cheap"].iloc[1] == "c"
    prem = M.premiums(prices, traded, xs["median_price"])
    assert prem["b"].iloc[1] == pytest.approx(0.01)
    assert np.isnan(prem["c"].iloc[4])


def test_dispersion_needs_two_live_sources():
    prices, traded = _panel()
    traded.iloc[0] = [True, False, False]
    xs = M.cross_section(prices, traded)
    assert np.isnan(xs["dispersion"].iloc[0])
    assert xs["median_price"].iloc[0] == 100


def test_arb_windows_contiguous_runs():
    prices, traded = _panel()
    xs = M.cross_section(prices, traded)
    w = M.arb_windows(xs, 0.005)
    assert len(w) == 1
    r = w.iloc[0]
    assert r["start"] == xs.index[1] and r["end"] == xs.index[2] + tu.BAR
    assert r["duration_min"] == 10 and r["max_dispersion"] == pytest.approx(0.02)
    assert r["rich_at_peak"] == "b" and r["cheap_at_peak"] == "c" and r["main_pair"] == "b > c"


def test_arb_windows_split_on_time_gap_and_threshold():
    ix = pd.DatetimeIndex([T0, T0 + tu.BAR, T0 + 4 * tu.BAR], tz="UTC")
    xs = pd.DataFrame({"dispersion": [0.01, 0.01, 0.01], "rich": "x", "cheap": "y", "n_live": 2}, index=ix)
    assert len(M.arb_windows(xs, 0.005)) == 2
    assert M.arb_windows(xs, 0.02).empty


def test_lead_lag_detects_leader():
    rng = np.random.default_rng(0)
    a = pd.Series(rng.normal(size=400))
    b = a.shift(2) + rng.normal(scale=0.2, size=400)     # b follows a by 2 bars
    res = M.lead_lag(a, b, 6)
    assert res["best_lag"] == 2 and res["best_corr"] > 0.9


# ---------------------------------------------------------------- grid / FX / time
def test_coarse_candles_land_on_last_slot():
    g = idx(6)
    df = pd.DataFrame({"ts": [g[0], g[3]], "open": 1.0, "high": 1.0, "low": 1.0, "close": [10.0, 11.0],
                       "volume": [1.0, 0.0], "volume_quote": [10.0, 0.0]})
    out = to_grid(df, g, "15m")
    assert out["close"].iloc[2] == 10.0 and np.isnan(out["close"].iloc[0])
    assert out["traded"].iloc[2] and not out["traded"].iloc[5]
    assert out["price"].iloc[5] == 10.0         # zero-volume print not used as a price


def test_fx_conversion_threshold():
    g = idx(3)
    frame = pd.DataFrame({"close": [100.0] * 3, "price": [100.0] * 3, "volume_quote": [1.0] * 3}, index=g)
    same, note = convert_usd(frame, pd.Series(1.0003, index=g), 5)
    assert same["price"].iloc[0] == 100.0 and "not converted" in note
    conv, _ = convert_usd(frame, pd.Series(0.998, index=g), 5)
    assert conv["price"].iloc[0] == pytest.approx(99.8)


def test_dst_session_times():
    assert tu.session_open("2026-09-10") == pd.Timestamp("2026-09-10 13:30", tz="UTC")   # EDT
    assert tu.session_open("2026-11-02") == pd.Timestamp("2026-11-02 14:30", tz="UTC")   # EST after Nov 1
    assert tu.fmt_vn(pd.Timestamp("2026-09-10 20:05", tz="UTC")) == "2026-09-11 03:05 VN"


def test_classify_night():
    earn = pd.DatetimeIndex([pd.Timestamp("2026-09-10 16:00", tz=tu.ET)])
    et, t, _ = classify_night(date(2026, 9, 10), date(2026, 9, 11), earn)
    assert et == "earnings_amc" and t == tu.et_clock_on("2026-09-10", 16)
    bmo = pd.DatetimeIndex([pd.Timestamp("2026-09-11 07:00", tz=tu.ET)])
    assert classify_night(date(2026, 9, 10), date(2026, 9, 11), bmo)[0] == "earnings_bmo"
    assert classify_night(date(2026, 9, 11), date(2026, 9, 14), pd.DatetimeIndex([], tz=tu.ET))[0] == "weekend"


def test_suffix_rules():
    rules = [{"suffix": "ON", "issuer": "ondo"}, {"suffix": "X", "issuer": "xstocks"}]
    assert _match_suffix("NVDAON", rules) == ("NVDA", "ondo")
    assert _match_suffix("NFLXX", rules) == ("NFLX", "xstocks")
    assert _match_suffix("NVDAx", rules) == ("NVDA", "xstocks")
    assert _match_suffix("BTC", rules) is None
