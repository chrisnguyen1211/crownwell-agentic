#!/usr/bin/env python3
import os
import json
from datetime import datetime

from dune_whale_tracker import DuneWhaleTracker
from etf_tracker_fixed import ETHETFFlowTracker
from etherscan_exchange_flows import EtherscanExchangeFlows


def main():
    # Prepare components
    whale = DuneWhaleTracker()
    etf = ETHETFFlowTracker()
    exch = EtherscanExchangeFlows()

    # Fetch data (graceful fallbacks)
    whale_data = whale.analyze_whale_activity()
    try:
        etf_data = etf.get_etf_flows_sync()
    except Exception:
        etf_data = {"daily_flow": 0, "flow_value": 0, "data_source": "error"}
    exchange_data = exch.get_exchange_flows(hours_back=72, min_eth=50.0)

    # Build daily analysis payload for storage
    analysis_payload = {
        "etf_flows": etf_data,
        "exchange_flows": {
            "net_flow": exchange_data.get("net_flow", 0.0),
            "inflow": exchange_data.get("inflow", 0.0),
            "outflow": exchange_data.get("outflow", 0.0),
            "exchanges": exchange_data.get("exchanges", {}),
            "data_source": exchange_data.get("data_source", "etherscan_txlist"),
        },
        "recommendation": {"action": "UNKNOWN", "confidence": 0, "score": {"bullish": 0, "bearish": 0, "neutral": 0}},
    }

    # Consolidated snapshot into new table yasuo_full_snapshot
    try:
        import requests
        import numpy as np
        SUPABASE_URL = os.getenv('SUPABASE_URL')
        SUPABASE_KEY = os.getenv('SUPABASE_KEY')
        headers = {
            'apikey': SUPABASE_KEY,
            'Authorization': f'Bearer {SUPABASE_KEY}',
            'Content-Type': 'application/json'
        }

        def sanitize(o):
            if isinstance(o, dict):
                return {k: sanitize(v) for k, v in o.items()}
            if isinstance(o, list):
                return [sanitize(v) for v in o]
            # numpy types
            try:
                if isinstance(o, (np.integer,)):
                    return int(o)
                if isinstance(o, (np.floating,)):
                    return float(o)
                if isinstance(o, (np.bool_,)):
                    return bool(o)
            except Exception:
                pass
            return o

        # Derive scalars
        overall_sentiment = None
        primary_signal = None
        confidence = None
        etf_daily_flow = float(etf_data.get('flow_value', etf_data.get('daily_flow', 0)) or 0)
        exchange_inflow_eth = float(exchange_data.get('inflow', 0) or 0)
        exchange_outflow_eth = float(exchange_data.get('outflow', 0) or 0)
        exchange_net_flow_eth = float(exchange_data.get('net_flow', 0) or 0)

        # Build payload
        row = sanitize({
            'created_at': datetime.utcnow().isoformat(),
            'overall_sentiment': overall_sentiment,
            'primary_signal': primary_signal,
            'confidence': confidence,
            'etf_daily_flow': etf_daily_flow,
            'exchange_inflow_eth': exchange_inflow_eth,
            'exchange_outflow_eth': exchange_outflow_eth,
            'exchange_net_flow_eth': exchange_net_flow_eth,
            'whale_intelligence': whale_data if isinstance(whale_data, dict) else {},
            'etf_flows': etf_data,
            'exchange_flows': exchange_data,
            'large_transactions': {},
            'market_context': {},
            'summary': {},
            'raw_run': {
                'whale': whale_data,
                'etf': etf_data,
                'exchange': exchange_data,
            }
        })

        # Insert
        url = f"{SUPABASE_URL}/rest/v1/yasuo_full_snapshot"
        resp = requests.post(url, headers=headers, data=json.dumps(row))
        print('yasup_full_snapshot insert:', resp.status_code, resp.text[:200])
    except Exception as e:
        print('Consolidated snapshot insert failed:', e)


if __name__ == "__main__":
    main()


