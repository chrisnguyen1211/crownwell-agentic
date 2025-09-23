#!/usr/bin/env python3
import os
import json
from pathlib import Path
import subprocess
import time
import streamlit as st
from datetime import datetime, timezone, timedelta

st.set_page_config(page_title="Trading Agents Workflow", layout="wide")

# Simple styles for highlights/badges/effects
st.markdown(
    """
    <style>
    .badge {display:inline-block;padding:4px 10px;border-radius:12px;font-size:12px;font-weight:600;margin-right:6px}
    .ok {background:#E6FFEC;color:#067D2B;border:1px solid #B7F0C2}
    .warn {background:#FFF6E6;color:#A15A00;border:1px solid #F7D7A5}
    .err {background:#FFECEC;color:#9F1A1A;border:1px solid #F4B7B7}
    .pill {background:#EEF2FF;color:#243B83;border:1px solid #C7D2FE}
    .rationale {background:#FAFAFA;border-left:4px solid #cbd5e1;padding:8px 10px;margin:6px 0;border-radius:6px;color:#000}
    .chat-scroll {height:380px;overflow-y:auto;padding:8px;background:#FAFAFA;border:1px solid #e5e7eb;border-radius:8px}
    .bubble-user {background:#e6f4ff;border:1px solid #bfdbfe;color:#0f172a;padding:8px 10px;border-radius:10px;margin:6px 0}
    .bubble-assistant {background:#f1f5f9;border:1px solid #e2e8f0;color:#0f172a;padding:8px 10px;border-radius:10px;margin:6px 0}
    </style>
    """,
    unsafe_allow_html=True,
)

REPORTS_DIR = Path(__file__).parent / "Reports"

def list_reports():
    # Sort by modified time (newest first)
    reports = list(REPORTS_DIR.glob("workflow_report_trading_agents_*.json"))
    reports.sort(key=lambda p: p.stat().st_mtime, reverse=True)
    return [str(p) for p in reports]

def load_report(path: str):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        st.error(f"Failed to load report: {e}")
        return {}

def render_node_status(report: dict):
    teams = report.get("teams", {})
    cols = st.columns(3)
    with cols[0]:
        st.subheader("Crawl Team")
        crawl = teams.get("crawl_team", {})
        status = crawl.get("status", "unknown")
        badge_cls = "ok" if status == "completed" else ("warn" if status == "partial" else "err")
        st.markdown(f"<span class='badge {badge_cls}'>Status: {status}</span>", unsafe_allow_html=True)
    with cols[1]:
        st.subheader("Alpha Team")
        alpha = teams.get("alpha_team", {})
        status = alpha.get("status", "unknown")
        badge_cls = "ok" if status == "completed" else ("warn" if status == "partial" else "err")
        st.markdown(f"<span class='badge {badge_cls}'>Status: {status}</span>", unsafe_allow_html=True)
    with cols[2]:
        st.subheader("Justin + Risk")
        jr = teams.get("justin_risk", {})
        status = jr.get("status", "unknown")
        badge_cls = "ok" if status == "completed" else ("warn" if status == "partial" else "err")
        st.markdown(f"<span class='badge {badge_cls}'>Status: {status}</span>", unsafe_allow_html=True)

def render_logs(report: dict):
    st.subheader("Agent logs")
    steps = report.get("detailed_steps", {})
    # Crawl mini-steps
    crawl = steps.get("step_1_crawl_team", {}).get("ministeps", {})
    with st.expander("Crawl Team ministeps", expanded=False):
        for name, mini in crawl.items():
            st.markdown(f"**{mini.get('agent', name)}** - {mini.get('status')}")
            st.code(mini.get("stdout_full", ""))
            st.code(mini.get("stderr_full", ""))
    # Alpha
    alpha = steps.get("step_2_alpha_team", {}).get("results", {})
    with st.expander("Alpha Team stdout/stderr", expanded=False):
        st.code(alpha.get("stdout_full", ""))
        st.code(alpha.get("stderr_full", ""))
    # Embedded full session
    session = alpha.get("alpha_debate_session", {})
    if session:
        with st.expander("Alpha Debate Session (full)", expanded=True):
            st.json(session)
    # Justin + Risk
    justin = steps.get("step_3_justin_risk", {}).get("results", {})
    with st.expander("Justin + Risk stdout/stderr", expanded=False):
        st.code(justin.get("stdout_full", ""))
        st.code(justin.get("stderr_full", ""))

def render_proposal(report: dict):
    st.subheader("Final Proposal")
    # Try to extract Justin verdict summaries from stdout
    justin = report.get("detailed_steps", {}).get("step_3_justin_risk", {}).get("results", {})
    stdout = justin.get("stdout_full", "")
    if stdout:
        st.text(stdout)
    else:
        st.info("No proposal text found in stdout. Check saved Supabase entries if needed.")

def render_text_report(report: dict):
    # Plain-text summary for non-technical viewers
    lines = []
    lines.append(f"Workflow ID: {report.get('workflow_id', '')}")
    lines.append(f"Overall Status: {report.get('overall_status', '')}")
    lines.append("")
    lines.append("Teams:")
    teams = report.get('teams', {})
    crawl = teams.get('crawl_team', {})
    alpha = teams.get('alpha_team', {})
    justin = teams.get('justin_risk', {})
    lines.append(f"- Crawl Team: {crawl.get('status', 'N/A')} (agents: {', '.join(crawl.get('agents', []))})")
    lines.append(f"- Alpha Team: {alpha.get('status', 'N/A')}")
    lines.append(f"- Justin + Risk: {justin.get('status', 'N/A')} (profile: {justin.get('risk_profile', 'N/A')})")
    lines.append("")
    lines.append("Detailed Steps:")
    steps = report.get('detailed_steps', {})
    # Crawl details
    s1 = steps.get('step_1_crawl_team', {})
    if s1:
        lines.append(f"1) Crawl Team: {s1.get('status', 'N/A')}")
        minis = s1.get('ministeps', {})
        for k, m in minis.items():
            agent = m.get('agent', k)
            status = m.get('status', 'N/A')
            duration = m.get('duration_seconds', 0)
            lines.append(f"   - {agent}: {status} ({int(duration)}s)")
            # Include brief stdout summary if available
            out = (m.get('stdout_full') or '').strip()
            if out:
                first_line = out.splitlines()[0][:160]
                lines.append(f"     · log: {first_line}")
    # Alpha details
    s2 = steps.get('step_2_alpha_team', {})
    if s2:
        lines.append(f"2) Alpha Team: {s2.get('status', 'N/A')}")
        # Human-readable summary (prefer embedded session JSON if available)
        res = s2.get('results', {})
        session = res.get('alpha_debate_session', {}) if isinstance(res.get('alpha_debate_session', {}), dict) else {}
        if session:
            winner = session.get('debate_winner', 'N/A')
            conf = session.get('confidence_level', 'N/A')
            data_sufficient = session.get('data_sufficient', None)
            if winner is not None:
                lines.append(f"   - Winner: {winner}")
            if conf is not None:
                lines.append(f"   - Confidence: {conf}")
            if data_sufficient is not None:
                lines.append(f"   - Data sufficient: {data_sufficient}")
            # Key arguments (concise bullets)
            key_args = session.get('key_arguments', {}) or {}
            bull_pts = key_args.get('bullish_key_points', []) or []
            bear_pts = key_args.get('bearish_key_points', []) or []
            for p in bull_pts[:3]:
                if isinstance(p, str) and p.strip():
                    lines.append(f"     · Bullish: {p.strip()}")
            for p in bear_pts[:3]:
                if isinstance(p, str) and p.strip():
                    lines.append(f"     · Bearish: {p.strip()}")
        else:
            # Fallback: parse from stdout markers (strip code blocks)
            stdout = (res.get('stdout_full', '') or '')
            if stdout:
                in_code = False
                for ln in stdout.splitlines():
                    s = ln.strip()
                    if s.startswith('```'):
                        in_code = not in_code
                        continue
                    if in_code:
                        continue
                    for marker in ["Winner:", "Confidence:", "Data Sufficient:"]:
                        if s.startswith(marker):
                            lines.append(f"   - {s}")
                            break
    # Justin details
    s3 = steps.get('step_3_justin_risk', {})
    if s3:
        lines.append(f"3) Justin + Risk: {s3.get('status', 'N/A')}")
        res = s3.get('results', {})
        stdout = res.get('stdout_full', '')
        if stdout:
            for marker in ["Justin Verdict:", "Confidence:", "Long-term Decision:", "Short-term Decision:"]:
                if marker in stdout:
                    for ln in stdout.splitlines():
                        if marker in ln:
                            lines.append(f"   - {ln.strip()}")
    # Final proposal text (best-effort from Justin stdout)
    if s3:
        res = s3.get('results', {})
        stdout = res.get('stdout_full', '')
        if stdout:
            lines.append("")
            lines.append("Proposal (from Justin + Risk):")
            # Extract a concise block around decisions
            snippet = []
            for ln in stdout.splitlines():
                if any(x in ln for x in ["Long-term Decision:", "Short-term Decision:", "Justin Verdict:"]):
                    snippet.append(ln.strip())
            if snippet:
                lines.extend([f"   - {s}" for s in snippet])
    lines.append("")
    lines.append(f"Summary: {report.get('summary', '')}")
    st.text("\n".join(lines))

def render_latest_proposal(report: dict):
    ts_raw = report.get('timestamp') or report.get('start_time') or ''
    # Convert to GMT+7 for display
    ts_disp = ts_raw
    try:
        dt = datetime.fromisoformat(ts_raw.replace('Z', '+00:00'))
        dt_gmt7 = dt.astimezone(timezone.utc) + timedelta(hours=7)
        ts_disp = dt_gmt7.strftime('%Y-%m-%d %H:%M:%S GMT+7')
    except Exception:
        pass
    st.subheader(f"Latest Proposal — {ts_disp}")
    steps = report.get('detailed_steps', {})
    s2 = steps.get('step_2_alpha_team', {}).get('results', {})
    s3 = steps.get('step_3_justin_risk', {}).get('results', {})

    # Extract from Justin stdout
    verdict = None
    confidence = None
    long_decision = None
    short_decision = None
    j_stdout = s3.get('stdout_full') or ''
    if j_stdout:
        for ln in j_stdout.splitlines():
            if ln.strip().startswith('Justin Verdict:'):
                verdict = ln.split(':',1)[1].strip()
            elif ln.strip().startswith('Confidence:'):
                try:
                    confidence = float(ln.split(':',1)[1].strip())
                except Exception:
                    confidence = None
            elif ln.strip().startswith('Long-term Decision:'):
                long_decision = ln.split(':',1)[1].strip()
            elif ln.strip().startswith('Short-term Decision:'):
                short_decision = ln.split(':',1)[1].strip()

    # Extract Alpha rationale (winner/confidence)
    alpha_winner = None
    alpha_conf = None
    a_stdout = s2.get('stdout_full') or ''
    if a_stdout:
        for ln in a_stdout.splitlines():
            if ln.strip().startswith('Winner:'):
                alpha_winner = ln.split(':',1)[1].strip()
            elif ln.strip().startswith('Confidence:'):
                try:
                    alpha_conf = float(ln.split(':',1)[1].strip())
                except Exception:
                    alpha_conf = None

    # Build rationales (concise bullets) from agents' workflow outputs
    rationales = []

    # Helper to add lines that look like reasons
    def should_include(line: str) -> bool:
        l = line.strip()
        if not l:
            return False
        # exclude headers and noise
        if any(h in l for h in ["CRAWLING", "INITIALIZING", "GENERATING SUMMARY", "ANALYZING", "TOTAL", "Method:", "Rate Limit:", "Target", "HTTP Request:"]):
            return False
        # include reasoning-like lines
        keys = ['reason', 'because', 'due to', 'driver', 'catalyst', 'risk', 'opportun', 'on-chain', 'whale', 'inflow', 'outflow', 'support', 'resistance', 'rsi', 'macd', 'breakout', 'divergence', 'fundamental', 'manipulation']
        return any(k in l.lower() for k in keys)

    # 1) Alpha debate key arguments from embedded session JSON if present
    alpha_session = steps.get('step_2_alpha_team', {}).get('results', {}).get('alpha_debate_session', {})
    if isinstance(alpha_session, dict):
        key_args = alpha_session.get('key_arguments', {}) or {}
        for bucket in ['bullish_key_points', 'bearish_key_points']:
            pts = key_args.get(bucket, []) or []
            for p in pts:
                if isinstance(p, str) and p.strip():
                    rationales.append(p.strip())
                if len(rationales) >= 6:
                    break
            if len(rationales) >= 6:
                break

    # 2) Justin + Risk: extract reasoning/risk/opportunity lines (no agent prefix)
    if len(rationales) < 6 and j_stdout:
        for ln in j_stdout.splitlines():
            if should_include(ln):
                rationales.append(ln.strip())
            if len(rationales) >= 6:
                break

    # 3) Crawl Team ministeps: extract actual content lines (no agent name)
    s1 = report.get('detailed_steps', {}).get('step_1_crawl_team', {})
    minis = s1.get('ministeps', {}) if isinstance(s1.get('ministeps', {}), dict) else {}
    for _, mini in minis.items():
        if len(rationales) >= 6:
            break
        out = (mini.get('stdout_full') or '')
        if not out:
            continue
        for ln in out.splitlines():
            if should_include(ln):
                txt = ln.strip()
                if txt not in rationales:
                    rationales.append(txt)
            if len(rationales) >= 6:
                break

    # Actions in horizontal layout
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Verdict", verdict or 'N/A')
    with col2:
        st.metric("Confidence", f"{confidence:.2f}" if isinstance(confidence, (int, float)) else 'N/A')
    with col3:
        st.metric("Long-term", long_decision or 'N/A')
    with col4:
        st.metric("Short-term", short_decision or 'N/A')
    
    # Rationales in horizontal layout
    st.markdown("**Rationales**")
    if rationales:
        cols = st.columns(min(len(rationales), 3))  # Max 3 columns
        for i, r in enumerate(rationales[:6]):
            with cols[i % 3]:
                st.markdown(f"<div class='rationale'>• {r}</div>", unsafe_allow_html=True)
    else:
        st.write("• No additional rationales parsed from logs")

st.title("📈 ETH Analysis Dashboard")
st.markdown("**Smart trading decisions powered by multiple AI agents**")

# Move "How it works" to the top for first-time viewers with an ETH chat box beside it
st.markdown("---")
top_left, top_right = st.columns(2)
with top_left:
    st.markdown("### 📈 How it works")
    st.markdown(
        """
        **Our AI agents work together:**
        - 🌸 Lily: Social sentiment (Twitter, Reddit, Telegram)
        - 📊 Bob: Technical indicators & signals
        - ⛓️ Yasuo: On-chain metrics & whale activity
        - 🎯 J97: Market manipulation/news signals
        - 🧠 Alpha Team: Bull vs Bear debate on 10-day data
        - ⚖️ Justin + Risk: Final decision & risk adjustments
        """
    )
with top_right:
    st.markdown("### 🤖 Ask about ETH")
    # Gemini chat focused on ETH (local only, reads from env or gemini_config.env)
    GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
    GEMINI_MODEL = os.environ.get("GEMINI_MODEL") or "gemini-2.5-flash"
    # Try to load from local gemini_config.env if not set
    if not GEMINI_API_KEY:
        try:
            cfg_path = Path(__file__).parent / "gemini_config.env"
            if cfg_path.exists():
                for line in cfg_path.read_text(encoding="utf-8").splitlines():
                    if line.startswith("GEMINI_API_KEY="):
                        GEMINI_API_KEY = line.split("=",1)[1].strip().strip('"')
                    elif line.startswith("GEMINI_MODEL=") and not os.environ.get("GEMINI_MODEL"):
                        GEMINI_MODEL = line.split("=",1)[1].strip().strip('"') or GEMINI_MODEL
        except Exception:
            pass

    # Chat history + input (two-box layout)
    if "eth_chat" not in st.session_state:
        st.session_state.eth_chat = []  # list of {role, content}

    # Upper: chat history (messages) in a fixed-height scroll area
    def render_chat_html(messages, trailing_assistant: str | None = None) -> str:
        parts = [
            """
<div id=\"chatScroll\" class=\"chat-scroll\">
"""
        ]
        for msg in messages[-200:]:
            role = msg.get("role", "assistant")
            content = msg.get("content", "")
            css = 'bubble-user' if role == 'user' else 'bubble-assistant'
            parts.append(f"<div class='{css}'>{content}</div>")
        if trailing_assistant is not None:
            parts.append(f"<div class='bubble-assistant'>{trailing_assistant}</div>")
        parts.append("""
</div>
<script>
  const box = document.getElementById('chatScroll');
  if (box) { box.scrollTop = box.scrollHeight; }
</script>
""")
        return "".join(parts)

    scroll_box = st.empty()
    scroll_box.markdown(render_chat_html(st.session_state.eth_chat), unsafe_allow_html=True)

    # Lower: input box
    user_q = st.chat_input("Ask me anything about ETH", key="eth_chat_input_box")

    def run_gemini(prompt: str) -> str:
        try:
            import google.generativeai as genai
        except Exception as e:
            return f"Gemini SDK not installed: {e}"
        if not GEMINI_API_KEY:
            return "Gemini chat is available locally only. No API key found."
        try:
            genai.configure(api_key=GEMINI_API_KEY)
            system_preamble = (
                "You are an assistant specialized in Ethereum (ETH). "
                "Answer concisely with facts. If the question is off-topic, steer back to ETH. "
                "Prefer recent market context and risk considerations."
            )
            from google.generativeai import GenerativeModel
            model = GenerativeModel(GEMINI_MODEL)
            history = []
            for m in st.session_state.eth_chat:
                role = "user" if m.get("role") == "user" else "model"
                history.append({"role": role, "parts": [m.get("content", "")]})
            chat = model.start_chat(history=history)
            resp = chat.send_message(system_preamble + "\n\nUser: " + prompt)
            text = getattr(resp, "text", None)
            if callable(text):
                text = resp.text()
            return text or "(no response)"
        except Exception as e:
            return f"Gemini error: {e}"

    if not GEMINI_API_KEY:
        st.info("Gemini chat is local-only. Please run locally with your gemini_config.env or GEMINI_API_KEY in env.")
    elif user_q:
        # Add user message
        st.session_state.eth_chat.append({"role": "user", "content": user_q})
        # Immediately show user's message pushed into chat pane
        scroll_box.markdown(render_chat_html(st.session_state.eth_chat), unsafe_allow_html=True)

        # Generate assistant reply
        answer_full = run_gemini(user_q)
        # Typing effect: progressively reveal within fixed scroll box
        revealed = ""
        for ch in answer_full or "":
            revealed += ch
            scroll_box.markdown(render_chat_html(st.session_state.eth_chat, trailing_assistant=revealed), unsafe_allow_html=True)
            time.sleep(0.01)
        # Save final assistant message and reset input box
        st.session_state.eth_chat.append({"role": "assistant", "content": answer_full})
        st.rerun()

st.markdown("---")

colA, colB = st.columns([3, 2])
with colA:
    st.markdown("### 🚀 Run Analysis")
    run_now = st.button("🔄 Run Full Analysis", type="primary", use_container_width=True)
    
    if run_now:
        st.info("🔄 Starting AI analysis... This may take 15-20 minutes")
    
    st.markdown("### 📊 Latest Results")
    report_files = list_reports()
    # Persist latest selection across refresh using session_state
    if 'selected_report' not in st.session_state:
        st.session_state.selected_report = report_files[0] if report_files else None
    # If current selected no longer exists (or first load), fallback to latest
    if st.session_state.selected_report not in report_files:
        st.session_state.selected_report = report_files[0] if report_files else None
    selected = st.session_state.selected_report
    if run_now:
        # Streaming run with live step progress + ETA (local only)
        try:
            cmd = ["python3", str((Path(__file__).parent / "run_complete_workflow.py")) , "--team", "all", "--risk-profile", "NEUTRAL"]
            proc = subprocess.Popen(cmd, cwd=str(Path(__file__).parent), stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1, universal_newlines=True)

            # Placeholders
            status_box = st.empty()
            header_box = st.empty()
            log_box = st.empty()
            crawl_ph = st.container()
            alpha_ph = st.container()
            justin_ph = st.container()

            # Progress bars per sub-step with rough ETA (seconds)
            eta_map = {
                "LILY": 15*60,
                "BOB": 20,
                "YASUO": 7*60,
                "J97": 40,
                "ALPHA": 3*60,
                "JUSTIN": 90,
            }
            current = None
            phase = None  # CRAWL / ALPHA / JUSTIN
            start_times = {}
            progress = {
                "LILY": crawl_ph.progress(0, text="LILY starting..."),
                "BOB": crawl_ph.progress(0, text="BOB waiting..."),
                "YASUO": crawl_ph.progress(0, text="YASUO waiting..."),
                "J97": crawl_ph.progress(0, text="J97 waiting..."),
                "ALPHA": alpha_ph.progress(0, text="ALPHA waiting..."),
                "JUSTIN": justin_ph.progress(0, text="JUSTIN waiting..."),
            }

            def tick(step_key: str):
                if not start_times.get(step_key):
                    start_times[step_key] = time.time()
                elapsed = time.time() - start_times[step_key]
                eta = max(eta_map.get(step_key, 60), 1)
                pct = min(int((elapsed/eta)*100), 99)
                progress[step_key].progress(pct, text=f"{step_key} running... ETA ~{int(max(eta-elapsed,0))}s")

            # Live log buffer
            live_logs = []

            for line in proc.stdout:
                line_s = line.rstrip()
                live_logs.append(line_s)
                # Detect phase switches
                if "STEP 1: CRAWL TEAM" in line_s:
                    phase = "CRAWL"
                elif "STEP 2: ALPHA TEAM" in line_s or "STARTING ALPHA TEAM" in line_s:
                    phase = "ALPHA"
                elif "STEP 3: JUSTIN + RISK TEAM" in line_s or "STARTING JUSTIN + RISK TEAM" in line_s:
                    phase = "JUSTIN"
                # Detect step switches
                if "Running LILY crawl agent" in line_s:
                    current = "LILY"
                    start_times[current] = time.time()
                elif "Running BOB crawl agent" in line_s:
                    current = "BOB"
                    start_times[current] = time.time()
                elif "Running YASUO crawl agent" in line_s:
                    current = "YASUO"
                    start_times[current] = time.time()
                elif "Running J97 crawl agent" in line_s:
                    current = "J97"
                    start_times[current] = time.time()
                elif "STARTING ALPHA TEAM" in line_s:
                    current = "ALPHA"
                    start_times[current] = time.time()
                elif "STARTING JUSTIN + RISK TEAM" in line_s:
                    current = "JUSTIN"
                    start_times[current] = time.time()

                # Update current step progress
                if current in progress:
                    tick(current)

                # Mark completions on standard messages
                if "completed successfully" in line_s:
                    # Try to infer which
                    for key in ["LILY","BOB","YASUO","J97","ALPHA","JUSTIN"]:
                        if key in line_s.upper():
                            progress[key].progress(100, text=f"{key} completed")

                # Render live
                header_text = f"Đang chạy: {current or (phase or 'khởi tạo')}"
                header_box.markdown(f"### {header_text}")
                status_box.info(f"Phase: {phase or 'initializing'} · Step: {current or '-'}")
                # Show last ~40 lines
                log_box.code("\n".join(live_logs[-40:]))

            ret = proc.wait()
            # Finalize all bars
            for key, bar in progress.items():
                bar.progress(100, text=f"{key} done")
            st.toast("Workflow finished", icon="✅" if ret == 0 else "⚠️")
            report_files = list_reports()
            if report_files:
                selected = report_files[0]
                st.session_state.selected_report = selected
        except Exception as e:
            st.error(f"Error running workflow: {e}")

with colB:
    st.markdown("### 💡 Trading Decision")
    if selected:
        report = load_report(selected)
        render_latest_proposal(report)
        st.markdown("### 📈 ETH Price Chart")
        chart_html = """
<div class="tradingview-widget-container">
  <div id="tradingview_1"></div>
  <script type="text/javascript" src="https://s3.tradingview.com/tv.js"></script>
  <script type="text/javascript">
  new TradingView.widget({
    "width": "100%",
    "height": 500,
    "symbol": "BINANCE:ETHUSDT",
    "interval": "60",
    "timezone": "Etc/UTC",
    "theme": "light",
    "style": "1",
    "locale": "en",
    "toolbar_bg": "#f1f3f6",
    "enable_publishing": false,
    "allow_symbol_change": true,
    "container_id": "tradingview_1"
  });
  </script>
</div>
"""
        st.components.v1.html(chart_html, height=520)

    else:
        st.info("👆 Run analysis to see trading recommendations")

st.divider()
if selected:
    report = load_report(selected)
    tabs = st.tabs(["📄 Simple Report", "🔍 Technical Details", "📊 Workflow Graph", "📝 Raw Logs"])
    with tabs[0]:
        render_text_report(report)
    with tabs[1]:
        render_proposal(report)
    with tabs[2]:
        try:
            dot = """
            digraph workflow {
              rankdir=LR;
              C [label="Crawl Team\n(Lily, Bob, Yasuo, J97)" shape=box];
              A [label="Alpha Team\n(Bull vs Bear)" shape=box];
              J [label="Justin + Risk" shape=box];
              C -> A [label="crawl data (10d)"];
              A -> J [label="debate summary + signals"];
              C -> J [label="context (10d)"];
            }
            """
            st.graphviz_chart(dot)
        except Exception as e:
            st.info(f"Graph render unavailable: {e}")
    with tabs[3]:
        render_logs(report)

