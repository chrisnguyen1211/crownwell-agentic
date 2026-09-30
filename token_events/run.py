#!/usr/bin/env python3
"""Tokenized-stock overnight event study across issuers.

  python run.py discover            # step 1: find sources + candidate events, write sources.yaml/events.yaml, STOP
  python run.py fetch   [--only ID] # step 2: crawl 5m candles into data/raw (cached)
  python run.py analyze [--only ID] # steps 3-4: normalize (k, FX) + metrics
  python run.py report  [--only ID] # step 5: report.html + summary.xlsx
  python run.py all     [--only ID] # fetch + analyze + report (uses the reviewed yaml files)
  python run.py demo                # synthetic event end-to-end in ./demo (no network)
"""
from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

from events import analyze, discover, excel, fetch, report  # noqa: E402
from events.config import Paths, load_config  # noqa: E402
from events.http import STATUS  # noqa: E402
from events.model import load_events, load_sources  # noqa: E402


def _setup_logging(paths: Paths, verbose: bool):
    paths.ensure()
    fmt = "%(asctime)s %(levelname)-7s %(name)s: %(message)s"
    logging.basicConfig(level=logging.DEBUG if verbose else logging.INFO, format=fmt, datefmt="%H:%M:%S",
                        handlers=[logging.StreamHandler(), logging.FileHandler(paths.data / "run.log")])
    for noisy in ("urllib3", "yfinance", "peewee"):
        logging.getLogger(noisy).setLevel(logging.WARNING)


def _load(paths, cfg):
    events = load_events(paths.events)
    for e in events:
        e.before_hours = cfg["window_before_hours"]
        e.after_open_hours = cfg["window_after_open_hours"]
    missing = [e.id for e in events if e.o1 is None]
    if missing:
        logging.warning("skipping events without O1 (next session not opened yet): %s", missing)
    events = [e for e in events if e.o1 is not None]
    sources, fx_cfg = load_sources(paths.sources)
    if not events:
        raise SystemExit(f"No events in {paths.events}. Run `python run.py discover` first.")
    return events, sources, fx_cfg


def _print_status(paths):
    print("\n==== Nguồn dữ liệu: lấy được / không lấy được ====")
    print(STATUS.table())
    STATUS.dump(paths.data / "source_status.csv")


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("cmd", choices=["discover", "fetch", "analyze", "report", "all", "demo"])
    ap.add_argument("--workdir", default=str(HERE), help="folder holding config/events/sources yaml + data/")
    ap.add_argument("--only", nargs="*", help="event ids or tickers to process (e.g. --only ORCL)")
    ap.add_argument("--refresh", action="store_true", help="ignore cache and download again")
    ap.add_argument("--today", help="override today's date (YYYY-MM-DD) for discover")
    ap.add_argument("-v", "--verbose", action="store_true")
    a = ap.parse_args(argv)

    if a.cmd == "demo":
        from events import demo

        root = Path(a.workdir) / "demo" if a.workdir == str(HERE) else Path(a.workdir)
        paths = Paths(root)
        _setup_logging(paths, a.verbose)
        demo.build(paths)
        a.cmd, a.workdir = "demo-run", str(root)
    paths = Paths(Path(a.workdir))
    _setup_logging(paths, a.verbose)
    cfg = load_config(paths)

    try:
        if a.cmd == "discover":
            import pandas as pd

            today = pd.Timestamp(a.today).date() if a.today else None
            cand, chosen = discover.run(paths, cfg, today)
            show = cand[cand["proposed"]] if cand["proposed"].any() else cand.head(15)
            cols = ["event_id", "cap_group", "event_type", "t_event_et", "t_event_vn", "close_before", "open_after",
                    "gap_pct", "n_issuers_with_data", "issuers", "resolution", "note"]
            with pd.option_context("display.max_colwidth", 70, "display.width", 250, "display.max_columns", 20):
                print("\n==== Đề xuất event (sửa events.yaml / sources.yaml rồi chạy `python run.py fetch`) ====")
                print(show[cols].to_string(index=False))
                print(f"\nTất cả ứng viên: {paths.candidates} ({len(cand)} dòng)")
                seeds = cand[cand["seed"]]
                if len(seeds):
                    print("\n---- Seed trong brief ----")
                    print(seeds[["event_id", "event_type", "gap_pct", "valid", "n_issuers_with_data",
                                 "note"]].to_string(index=False))
            print(f"\nĐÃ DỪNG để duyệt: {paths.events} và {paths.sources}")
            return
        events, sources, fx_cfg = _load(paths, cfg)
        if a.cmd in ("fetch", "all"):
            fetch.run(paths, cfg, events, sources, fx_cfg, a.refresh, a.only)
        if a.cmd in ("analyze", "all", "demo-run"):
            analyze.run(paths, cfg, events, sources, fx_cfg, a.only)
        if a.cmd in ("report", "all", "demo-run"):
            ids = [e.id for e in events if not a.only or e.id in a.only or e.ticker in a.only]
            print("report:", report.build(paths, cfg, ids))
            print("excel: ", excel.build(paths, cfg, ids))
    finally:
        _print_status(paths)


if __name__ == "__main__":
    main()
