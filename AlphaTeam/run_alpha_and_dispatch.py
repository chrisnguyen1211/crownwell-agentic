#!/usr/bin/env python3
import os, json, subprocess, sys
from datetime import datetime

BASE = "/Users/nguyenhuycuong/Crownwell agentic/TradingAgents"
ALPHA_DIR = os.path.join(BASE, 'AlphaTeam')

alpha_script = os.path.join(ALPHA_DIR, 'run_alpha.py')
dispatch_script = os.path.join(ALPHA_DIR, 'dispatch_requests.py')

# 1) Run Alpha to generate a new debate file
res = subprocess.run([sys.executable, alpha_script], cwd=ALPHA_DIR, capture_output=True, text=True)
print(res.stdout)
print(res.stderr, file=sys.stderr)

# 2) Load latest Alpha JSON and check if there are any requests
files = sorted([f for f in os.listdir(ALPHA_DIR) if f.startswith('alpha_debate_') and f.endswith('.json')])
if not files:
    print('No alpha debate file found after run. Skip dispatcher.')
    sys.exit(0)
latest = os.path.join(ALPHA_DIR, files[-1])
with open(latest) as f:
    alpha = json.load(f)

bull_reqs = alpha.get('bullish', {}).get('requests') or []
bear_reqs = alpha.get('bearish', {}).get('requests') or []

if len(bull_reqs) + len(bear_reqs) == 0:
    print('No requests present. Dispatcher will not run.')
    sys.exit(0)

# 3) Run dispatcher only if requests exist
print('Requests detected. Running dispatcher...')
res2 = subprocess.run([dispatch_script], cwd=ALPHA_DIR, capture_output=True, text=True)
print(res2.stdout)
print(res2.stderr, file=sys.stderr)
