"""Time helpers: UTC storage, ET/VN display, US session boundaries, 5-minute grid."""
from __future__ import annotations

from datetime import date, datetime, time, timedelta

import pandas as pd

ET = "America/New_York"   # handles US DST (after the first Sunday of Nov, ET = UTC-5)
VN = "Asia/Ho_Chi_Minh"   # UTC+7, no DST
BAR = pd.Timedelta(minutes=5)

OPEN_T = time(9, 30)
CLOSE_T = time(16, 0)
PRE_T = time(4, 0)
POST_END_T = time(20, 0)


def utc(ts) -> pd.Timestamp:
    """Any timestamp-like -> tz-aware UTC Timestamp. Naive input is assumed to be UTC."""
    t = pd.Timestamp(ts)
    return t.tz_localize("UTC") if t.tzinfo is None else t.tz_convert("UTC")


def et_at(d: date | str, t: time) -> pd.Timestamp:
    """Wall-clock time `t` in New York on day `d`, returned in UTC (DST-correct)."""
    d = pd.Timestamp(d).date()
    return pd.Timestamp(datetime.combine(d, t)).tz_localize(ET).tz_convert("UTC")


def session_open(d) -> pd.Timestamp:
    return et_at(d, OPEN_T)


def session_close(d) -> pd.Timestamp:
    return et_at(d, CLOSE_T)


def fmt_et(ts) -> str:
    return utc(ts).tz_convert(ET).strftime("%Y-%m-%d %H:%M %Z")


def fmt_vn(ts) -> str:
    return utc(ts).tz_convert(VN).strftime("%Y-%m-%d %H:%M") + " VN"


def fmt_utc(ts) -> str:
    return utc(ts).strftime("%Y-%m-%d %H:%M UTC")


def floor5(ts) -> pd.Timestamp:
    return utc(ts).floor("5min")


def grid(start, end) -> pd.DatetimeIndex:
    """Common 5-minute grid (bar *open* times, UTC) covering [start, end)."""
    return pd.date_range(floor5(start), floor5(utc(end) - pd.Timedelta(seconds=1)), freq="5min", tz="UTC")


def us_session_label(ts) -> str:
    """regular / pre / post / closed for a UTC bar-open timestamp (ignores holidays)."""
    t = utc(ts).tz_convert(ET)
    if t.weekday() >= 5:
        return "closed"
    hm = t.time()
    if OPEN_T <= hm < CLOSE_T:
        return "regular"
    if PRE_T <= hm < OPEN_T:
        return "pre"
    if CLOSE_T <= hm < POST_END_T:
        return "post"
    return "closed"


def et_clock_on(d, hh: int, mm: int = 0) -> pd.Timestamp:
    return et_at(d, time(hh, mm))


def to_et_naive(idx: pd.DatetimeIndex) -> pd.DatetimeIndex:
    """For plotting: ET wall-clock without tz so axes read in ET."""
    return idx.tz_convert(ET).tz_localize(None)


def add_display_cols(df: pd.DataFrame, col: str = "ts") -> pd.DataFrame:
    out = df.copy()
    s = pd.to_datetime(out[col], utc=True)
    out[col + "_et"] = s.dt.tz_convert(ET).dt.strftime("%Y-%m-%d %H:%M")
    out[col + "_vn"] = s.dt.tz_convert(VN).dt.strftime("%Y-%m-%d %H:%M")
    return out


def next_weekday(d: date) -> date:
    d = d + timedelta(days=1)
    while d.weekday() >= 5:
        d += timedelta(days=1)
    return d
