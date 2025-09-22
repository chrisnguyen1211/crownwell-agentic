#!/usr/bin/env python3
import os, json, logging
from datetime import datetime
from dotenv import load_dotenv
from supabase import create_client

# Load shared env from J97
load_dotenv(os.path.join(os.path.dirname(__file__), '..', 'J97', 'api_keys.env'))
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('alpha')

SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_KEY = os.getenv('SUPABASE_KEY')

# Sanitize URL (handle accidental leading characters)
if SUPABASE_URL:
    SUPABASE_URL = SUPABASE_URL.strip()
    if SUPABASE_URL.startswith('@'):
        SUPABASE_URL = SUPABASE_URL[1:]

def _safe_create_client(url, key):
    try:
        if not url or not key or not (url.startswith('http://') or url.startswith('https://')):
            return None
        return create_client(url, key)
    except Exception:
        return None

client = _safe_create_client(SUPABASE_URL, SUPABASE_KEY)


def fetch_latest():
    # If Supabase client is available, try remote
    if client is not None:
        try:
            j97 = client.table('j97_daily_reports').select('*').order('created_at').limit(1).execute().data
        except Exception:
            j97 = []
        try:
            yasuo = client.table('yasuo_full_snapshot').select('*').order('created_at').limit(1).execute().data
        except Exception:
            yasuo = []
        try:
            lily = client.table('lily_aggregated_sentiment').select('*').order('created_at').limit(1).execute().data
        except Exception:
            lily = []
        bob = {}
        if j97 or yasuo or lily:
            return (j97[-1] if j97 else {}), (yasuo[-1] if yasuo else {}), (lily[-1] if lily else {}), bob

    # Fallback to local latest files if Supabase unavailable/invalid
    base = os.path.join(os.path.dirname(__file__), '..')
    reports_dir = os.path.join(base, 'Reports')
    yasuo_dir = os.path.join(base, 'Yasuo - Onchain analyst')

    # J97 local fallback (latest j97_* summary if exists)
    j97_local = {}
    try:
        candidates = [f for f in os.listdir(os.path.join(base, 'J97')) if f.startswith('j97_analysis_summary_') and f.endswith('.json')]
        candidates.sort()
        if candidates:
            with open(os.path.join(base, 'J97', candidates[-1]), 'r') as f:
                j97_local = __import__('json').load(f)
    except Exception:
        pass

    # Yasuo local latest
    yasuo_local = {}
    try:
        yfiles = [f for f in os.listdir(yasuo_dir) if f.startswith('yasuo_real_data_') and f.endswith('.json')]
        yfiles.sort()
        if yfiles:
            with open(os.path.join(yasuo_dir, yfiles[-1]), 'r') as f:
                yasuo_local = __import__('json').load(f).get('data_sources', {})
    except Exception:
        pass

    # Lily local fallback not essential
    lily_local = {}

    bob = {}
    return j97_local, yasuo_local, lily_local, bob


def build_cases():
    j97, yasuo, lily, bob = fetch_latest()
    bullish = {
        'thesis': 'ETH upside with flows/sentiment tailwinds',
        'evidence': {
            'news': j97,
            'onchain': (yasuo.get('exchange_flows') if isinstance(yasuo, dict) else {}),
            'etf': (yasuo.get('etf_flows') if isinstance(yasuo, dict) else {}),
            'social': lily,
            'technicals': bob,
        },
        'requests': [
            'J97: ETF creations/redemptions detail and ETH-specific share',
            'Lily: 24h/7d sentiment deltas with bot filtering score',
            'Bob: MA(20/50/200), RSI/MACD across 4H/D/W, volume profile',
            'Yasuo: 1h/4h exchange net flows, whale accumulation vs distribution',
        ]
    }
    bearish = {
        'thesis': 'Crowded optimism; divergence risks and headline fragility',
        'evidence': {
            'news': j97,
            'onchain': (yasuo.get('exchange_flows') if isinstance(yasuo, dict) else {}),
            'etf': (yasuo.get('etf_flows') if isinstance(yasuo, dict) else {}),
            'social': lily,
            'technicals': bob,
        },
        'requests': [
            'J97: Distinguish ETH-specific fundamentals vs market-wide headlines',
            'Lily: Account quality and concentration metrics',
            'Bob: Multi-TF divergences; HVN/LVN levels',
            'Yasuo: Intraday exchange inflow spikes; CEX/DEX split',
        ]
    }
    rounds = [
        {'bullish':'Outflows+ETF narrative+HTF uptrend', 'bearish':'Outflows ambiguous; divergences; headline risk'},
        {'bullish':'If creations persist and no inflow spikes, buy dips', 'bearish':'If inflows rise near resistances, fade strength'},
    ]
    out = {
        'timestamp': datetime.utcnow().isoformat(),
        'bullish': bullish,
        'bearish': bearish,
        'debate_rounds': rounds,
    }
    return out

if __name__ == '__main__':
    debate = build_cases()
    fn = os.path.join(os.path.dirname(__file__), f"alpha_debate_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.json")
    with open(fn, 'w') as f:
        json.dump(debate, f, ensure_ascii=False, indent=2)
    logger.info('Alpha debate saved to %s', fn)
