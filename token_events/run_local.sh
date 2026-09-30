#!/usr/bin/env bash
# One-shot for running on your own machine:
#   setup venv -> discover (step 1) -> push results to the branch so they can be reviewed.
# Usage (from the repo root):  bash token_events/run_local.sh            # discover only
#                              bash token_events/run_local.sh ORCL       # + fetch/analyze/report for one ticker
set -euo pipefail
cd "$(dirname "$0")"
BRANCH=claude/cool-thompson-goskw5

PY=${PYTHON:-}
if [ -z "$PY" ]; then
  for c in python3.13 python3.12 python3.11 python3; do
    if command -v "$c" >/dev/null && "$c" -c 'import sys; sys.exit(sys.version_info < (3, 11))'; then PY=$c; break; fi
  done
fi
[ -n "$PY" ] || { echo "Cần Python >= 3.11 (đặt PYTHON=/đường/dẫn/python3.11)"; exit 1; }

[ -d .venv-events ] || "$PY" -m venv .venv-events
. .venv-events/bin/activate
pip install -q --upgrade pip
pip install -q -r requirements.txt

python run.py discover 2>&1 | tee data_discover_console.log || true

if [ "${1:-}" != "" ]; then
  python run.py all --only "$1" 2>&1 | tee -a data_discover_console.log || true
fi

# Share results on the branch (outputs are git-ignored, so force-add just these files)
mkdir -p results
cp -f events_candidates.csv events.yaml sources.yaml results/ 2>/dev/null || true
cp -f data/run.log data/source_status.csv results/ 2>/dev/null || true
mv -f data_discover_console.log results/console.log
[ -f report.html ] && cp -f report.html summary.xlsx results/ || true
git add -f results
if git diff --cached --quiet; then echo "Không có gì mới để commit."; exit 0; fi
git commit -q -m "token_events: discover results from local run"
git push origin "HEAD:$BRANCH"
echo "Đã đẩy kết quả lên branch $BRANCH (token_events/results/)."
