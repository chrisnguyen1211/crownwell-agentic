#!/usr/bin/env python3
"""
Risk Team module
Evaluates ETH risk across short/mid/long horizons with three risk modes
(aggressive, neutral, conservative) and adjusts Justin's proposal if needed.
"""

import os
import json
from datetime import datetime
from typing import Dict, Any

BASE = "/Users/nguyenhuycuong/Crownwell agentic/TradingAgents"
JUSTIN_DIR = os.path.join(BASE, 'JustinLy')
YASUO_DIR = os.path.join(BASE, 'Yasuo - Onchain analyst')


class RiskAssessor:
    def __init__(self, mode: str = "neutral") -> None:
        self.mode = mode.lower()  # aggressive | neutral | conservative

    def _latest_file(self, directory: str, prefix: str, suffix: str) -> str | None:
        files = [f for f in os.listdir(directory) if f.startswith(prefix) and f.endswith(suffix)]
        if not files:
            return None
        files.sort()
        return os.path.join(directory, files[-1])

    def load_inputs(self) -> Dict[str, Any]:
        data: Dict[str, Any] = {}
        # Justin verdict
        jfile = self._latest_file(JUSTIN_DIR, 'justin_verdict_', '.json')
        if jfile:
            with open(jfile, 'r') as f:
                data['justin'] = json.load(f)
            data['justin_file'] = jfile
        # Yasuo latest onchain snapshot
        yfile = self._latest_file(YASUO_DIR, 'yasuo_real_data_', '.json')
        if yfile:
            with open(yfile, 'r') as f:
                data['yasuo'] = json.load(f)
            data['yasuo_file'] = yfile
        return data

    def assess(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        justin = inputs.get('justin', {})
        yasuo = inputs.get('yasuo', {})

        # Baseline from Justin
        verdict = justin.get('verdict', 'HOLD')
        confidence = float(justin.get('confidence', 0.5) or 0.5)
        proposal = justin.get('proposal', {})

        # Risk metrics from Yasuo
        ds = yasuo.get('data_sources', {})
        etf = ds.get('etf_flows', {})
        exch = ds.get('exchange_flows', {})
        live = ds.get('liveliness', {})

        etf_daily = float(etf.get('daily_flow', 0) or 0)
        net_flow_eth = float(exch.get('net_flow', 0) or 0)
        liveliness_score = float(live.get('liveliness_score', 0.5) or 0.5)

        # Compute horizon risks (simple heuristics)
        short_risk = 'LOW'
        mid_risk = 'LOW'
        long_risk = 'LOW'

        # Short-term risk responds to exchange flows and liveliness swings
        if abs(net_flow_eth) > 15000 or liveliness_score < 0.4:
            short_risk = 'HIGH'
        elif abs(net_flow_eth) > 5000 or liveliness_score < 0.5:
            short_risk = 'MEDIUM'

        # Mid-term risk responds to ETF flows and liveliness trend proxy
        if etf_daily < -150_000_000:
            mid_risk = 'HIGH'
        elif etf_daily < -50_000_000:
            mid_risk = 'MEDIUM'

        # Long-term risk responds to sustained ETF inflows proxy and neutral liveliness
        if etf_daily > 250_000_000 and liveliness_score >= 0.55:
            long_risk = 'LOW'
        elif etf_daily < 0:
            long_risk = 'MEDIUM'

        # Adjust proposal based on mode
        adjusted = self._adjust_proposal(proposal, verdict, confidence, short_risk, mid_risk, long_risk)
        need_redispatch = (short_risk == 'HIGH') or (mid_risk == 'HIGH')

        return {
            'timestamp': datetime.utcnow().isoformat(),
            'mode': self.mode,
            'inputs': {
                'justin_file': inputs.get('justin_file'),
                'yasuo_file': inputs.get('yasuo_file'),
                'etf_daily': etf_daily,
                'exchange_net_flow_eth': net_flow_eth,
                'liveliness_score': liveliness_score
            },
            'risk': {
                'short_term': short_risk,
                'mid_term': mid_risk,
                'long_term': long_risk
            },
            'adjusted_actions': adjusted,
            'need_redispatch': need_redispatch
        }

    def _adjust_proposal(self, proposal: Dict[str, Any], verdict: str, confidence: float,
                          short_risk: str, mid_risk: str, long_risk: str) -> Dict[str, Any]:
        portfolio = proposal.get('portfolio', {
            'decision': verdict,
            'style': 'hold' if verdict == 'HOLD' else verdict.lower(),
            'confidence': confidence,
            'horizon': 'long-term'
        })
        trading = proposal.get('trading', {
            'mode': 'short-term',
            'entry': {'type': 'scaled', 'tranches': 3, 'risk_profile': 'neutral'},
            'risk': {'stop_loss_pct': 0.02, 'take_profit_pct': 0.04, 'rr_min': 1.5}
        })

        # Map mode and risks to sizing and protection
        risk_mult = {'aggressive': 1.2, 'neutral': 1.0, 'conservative': 0.8}.get(self.mode, 1.0)

        # Adjust stop/take based on risk horizons
        sl = trading['risk']['stop_loss_pct']
        tp = trading['risk']['take_profit_pct']

        if short_risk == 'HIGH':
            sl *= 0.8  # tighter
            tp *= 0.9
        elif short_risk == 'MEDIUM':
            sl *= 0.9

        if mid_risk == 'HIGH':
            portfolio['style'] = 'partial sell' if verdict != 'SELL' else 'sell'
        elif mid_risk == 'MEDIUM' and verdict == 'BUY':
            portfolio['style'] = 'DCA buy'

        # Apply mode multiplier to tranche count (risk allocation)
        tranches = max(1, int(trading['entry'].get('tranches', 3) * risk_mult))

        trading['entry']['tranches'] = tranches
        trading['entry']['risk_profile'] = self.mode
        trading['risk']['stop_loss_pct'] = round(sl, 4)
        trading['risk']['take_profit_pct'] = round(tp, 4)

        return {'portfolio': portfolio, 'trading': trading}


def main(mode: str = "neutral") -> Dict[str, Any]:
    assessor = RiskAssessor(mode=mode)
    inputs = assessor.load_inputs()
    result = assessor.assess(inputs)

    out_file = os.path.join(BASE, 'Reports', f"risk_assessment_{mode}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.json")
    os.makedirs(os.path.dirname(out_file), exist_ok=True)
    with open(out_file, 'w') as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    print(f"✅ Risk assessment saved to {out_file}")
    return result


if __name__ == '__main__':
    import sys
    mode = sys.argv[1] if len(sys.argv) > 1 else 'neutral'
    main(mode)


