#!/usr/bin/env python3
"""
Aggregate Lily sentiment across platforms and insert one snapshot into lily_aggregated_sentiment.
Uses Supabase REST API with SUPABASE_URL and SUPABASE_KEY (service key).
Aggregates last N hours (default 6).
"""
import os
import sys
import math
import json
import requests
from datetime import datetime, timedelta, timezone
from collections import Counter


def supa_headers():
    key = os.getenv('SUPABASE_KEY')
    return {
        'apikey': key,
        'Authorization': f'Bearer {key}',
        'Content-Type': 'application/json'
    }


def fetch_posts(table: str, since_iso: str, ts_field: str) -> list:
    url = f"{os.getenv('SUPABASE_URL')}/rest/v1/{table}"
    # filter by timestamp >= since
    params = {
        'select': '*',
        f'{ts_field}': f'gte.{since_iso}',
        'limit': 10000,
        'order': f'{ts_field}.desc'
    }
    r = requests.get(url, headers=supa_headers(), params=params, timeout=60)
    r.raise_for_status()
    return r.json()


def avg(values):
    values = [v for v in values if isinstance(v, (int, float)) and not (isinstance(v, float) and (math.isnan(v) or math.isinf(v)))]
    return (sum(values) / len(values)) if values else None


def main(hours: int = 6):
    base = os.getenv('SUPABASE_URL'); key = os.getenv('SUPABASE_KEY')
    if not base or not key:
        print('❌ SUPABASE_URL/SUPABASE_KEY not set'); sys.exit(1)

    since = datetime.now(timezone.utc) - timedelta(hours=hours)
    since_iso = since.isoformat()

    tw = fetch_posts('twitter_posts', since_iso, 'tweet_timestamp')
    rd = fetch_posts('reddit_posts', since_iso, 'post_timestamp')
    tg = fetch_posts('telegram_posts', since_iso, 'message_timestamp')

    def sentiments(rows, field='sentiment_score'):
        return [float(r.get(field, 0) or 0) for r in rows]

    def keywords(rows):
        c = Counter()
        for r in rows:
            kws = r.get('keywords_detected') or []
            if isinstance(kws, str):
                # handle potential string JSON
                try:
                    kws = json.loads(kws)
                except Exception:
                    kws = []
            for k in kws:
                if k:
                    c[k] += 1
        # return top 15
        return [{'keyword': k, 'count': n} for k, n in c.most_common(15)]

    twitter_avg = avg(sentiments(tw))
    reddit_avg = avg(sentiments(rd))
    telegram_avg = avg(sentiments(tg))
    all_scores = [s for s in (sentiments(tw) + sentiments(rd) + sentiments(tg))]
    overall = avg(all_scores)

    platform_breakdown = {
        'twitter': {'count': len(tw), 'avg': twitter_avg},
        'reddit': {'count': len(rd), 'avg': reddit_avg},
        'telegram': {'count': len(tg), 'avg': telegram_avg},
    }

    top_kw = keywords(tw + rd + tg)

    row = {
        'created_at': datetime.now(timezone.utc).isoformat(),
        'total_posts': len(tw) + len(rd) + len(tg),
        'overall_sentiment': overall,
        'avg_sentiment': overall,  # same metric here
        'twitter_count': len(tw),
        'reddit_count': len(rd),
        'telegram_count': len(tg),
        'twitter_avg': twitter_avg,
        'reddit_avg': reddit_avg,
        'telegram_avg': telegram_avg,
        'platform_breakdown': platform_breakdown,
        'top_keywords': top_kw,
        'samples': {
            'twitter': tw[:3],
            'reddit': rd[:3],
            'telegram': tg[:3]
        }
    }

    url = f"{base}/rest/v1/lily_aggregated_sentiment"
    resp = requests.post(url, headers=supa_headers(), data=json.dumps(row))
    print('Insert aggregated:', resp.status_code, resp.text[:200])


if __name__ == '__main__':
    hours = int(os.getenv('LILY_AGG_WINDOW_HOURS', '6'))
    main(hours)


