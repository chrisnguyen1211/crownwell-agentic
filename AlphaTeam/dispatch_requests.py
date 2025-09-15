#!/usr/bin/env python3
import os, json, subprocess, shlex, time
from datetime import datetime
from dotenv import load_dotenv

BASE = "/Users/nguyenhuycuong/Crownwell agentic/TradingAgents"
ALPHA_DIR = os.path.join(BASE, 'AlphaTeam')
REPORTS_DIR = os.path.join(BASE, 'Reports')
J97_DIR = os.path.join(BASE, 'J97')
LILY_DIR = os.path.join(BASE, 'Lily')
BOB_DIR = os.path.join(BASE, 'Bob')
YASUO_DIR = os.path.join(BASE, 'Yasuo - Onchain analyst')

# Load shared env
load_dotenv(os.path.join(J97_DIR, 'api_keys.env'))


def find_latest_alpha():
    files = sorted([f for f in os.listdir(ALPHA_DIR) if f.startswith('alpha_debate_') and f.endswith('.json')])
    if not files:
        raise SystemExit('No alpha debate file found')
    path = os.path.join(ALPHA_DIR, files[-1])
    with open(path) as f:
        return json.load(f), path


def run_cmd(cmd, cwd=None, timeout=120):
    try:
        proc = subprocess.run(cmd, cwd=cwd, shell=True, capture_output=True, text=True, timeout=timeout)
        return {'ok': proc.returncode == 0, 'code': proc.returncode, 'stdout': proc.stdout[-4000:], 'stderr': proc.stderr[-4000:]}
    except subprocess.TimeoutExpired as e:
        return {'ok': False, 'code': -1, 'stdout': (e.stdout or '')[-4000:], 'stderr': f'timeout after {timeout}s'}


def plan_runs(requests):
    want = set()
    for r in requests:
        txt = (r or '').lower()
        if 'j97' in txt or 'etf' in txt or 'news' in txt:
            want.add('j97')
        if 'lily' in txt or 'sentiment' in txt or 'influencer' in txt:
            want.add('lily')
        if 'bob' in txt or 'rsi' in txt or 'macd' in txt or 'ma(' in txt or 'ema' in txt:
            want.add('bob')
        if 'yasuo' in txt or 'exchange flow' in txt or 'whale' in txt or 'staking' in txt:
            want.add('yasuo')
    return sorted(want)


def main():
    alpha, alpha_path = find_latest_alpha()
    bullish_req = alpha.get('bullish', {}).get('requests') or []
    bearish_req = alpha.get('bearish', {}).get('requests') or []
    targets = plan_runs(bullish_req + bearish_req)

    results = {'timestamp': datetime.utcnow().isoformat(), 'alpha_file': alpha_path, 'targets': targets, 'runs': {}}

    # Commands per agent (use existing single-run entrypoints)
    cmds = {
        'j97': f"source '{BASE}/j97_venv/bin/activate' && python3 run_j97.py --mode single",
        'lily': f"source '{BASE}/lily_venv/bin/activate' && python3 run_lily.py",
        'bob': f"source '{BASE}/bob_venv/bin/activate' && python3 run_bob.py",
        'yasuo': f"python3 demo_real_data.py",
    }
    cwds = {
        'j97': J97_DIR,
        'lily': LILY_DIR,
        'bob': BOB_DIR,
        'yasuo': YASUO_DIR,
    }

    for t in targets:
        cmd = cmds.get(t)
        if not cmd:
            continue
        res = run_cmd(cmd, cwd=cwds[t], timeout=999999 if t in ('lily','yasuo') else 240)
        results['runs'][t] = res

    os.makedirs(REPORTS_DIR, exist_ok=True)
    out = os.path.join(REPORTS_DIR, f"alpha_dispatch_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.json")
    with open(out, 'w') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    print(out)

if __name__ == '__main__':
    main()
