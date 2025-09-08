#!/usr/bin/env python3
"""
ETH Trading Framework - Web UI
Real-time workflow visualization
"""
import os
from dotenv import load_dotenv
import sys
import json
import threading
import time
from datetime import datetime
from flask import Flask, render_template, jsonify, request
import httpx

# Load env from project root .env if available
try:
    load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '..', '.env'))
    load_dotenv()
except Exception:
    pass

# Load Supabase env if present (prefer service key)
SUPABASE_URL = os.getenv('SUPABASE_URL') or 'https://pgjorocqnafmvcsjhulu.supabase.co'
SUPABASE_KEY = os.getenv('SUPABASE_SERVICE_KEY') or os.getenv('SUPABASE_KEY')
from flask_socketio import SocketIO, emit

app = Flask(__name__)
app.config['SECRET_KEY'] = 'eth_trading_framework_2025'
socketio = SocketIO(app, cors_allowed_origins="*")

# Global state
workflow_state = {
    'status': 'idle',
    'current_stage': None,
    'results': {},
    'start_time': None,
    'logs': []
}

class MockAgent:
    def __init__(self, name, role):
        self.name = name
        self.role = role
        self.status = 'idle'
        self.progress = 0
        
    def update_status(self, status, progress=None, task=None):
        self.status = status
        if progress is not None:
            self.progress = progress
            
        socketio.emit('agent_update', {
            'agent': self.name,
            'status': status,
            'progress': self.progress,
            'task': task or f'{status}...',
            'timestamp': datetime.now().isoformat()
        })
        
        log_entry = f"[{datetime.now().strftime('%H:%M:%S')}] {self.name}: {status}"
        if task:
            log_entry += f" - {task}"
        workflow_state['logs'].append(log_entry)
        socketio.emit('log_update', {'log': log_entry})
    
    def analyze(self, crypto_symbol):
        steps = [
            (20, f'Fetching {crypto_symbol} data'),
            (50, f'Processing {self.role}'),
            (80, 'Generating analysis'),
            (100, f'{self.role} completed')
        ]
        
        for progress, task in steps:
            self.update_status('running', progress, task)
            time.sleep(0.8)
        
        # Mock analysis
        if "fundamentals" in self.role.lower():
            analysis = f"📊 {crypto_symbol} Fundamentals:\\n- Price: $3,750 (+2.5%)\\n- Market Cap: $450B\\n- Volume: $15B\\n- Network health: Strong"
        elif "liquidity" in self.role.lower():
            analysis = f"💧 {crypto_symbol} Liquidity:\\n- DEX TVL: $2.5B\\n- Slippage: 0.05%\\n- Order depth: Excellent"
        elif "bull" in self.role.lower():
            analysis = f"🐂 {crypto_symbol} Bull Case:\\n- Strong fundamentals\\n- Technical breakout\\n- Recommendation: BUY"
        elif "bear" in self.role.lower():
            analysis = f"🐻 {crypto_symbol} Bear Case:\\n- Regulatory risks\\n- Market volatility\\n- Recommendation: CAUTION"
        elif "trading" in self.role.lower():
            analysis = f"📋 {crypto_symbol} Trading Strategy:\\n- Entry: $3,750\\n- Target: $3,900\\n- Stop Loss: $3,600"
        else:
            analysis = f"👨‍💼 {crypto_symbol} Portfolio Decision:\\n- Risk: Moderate\\n- Allocation: 10%\\n- Status: APPROVED"
        
        self.update_status('completed', 100, f'{self.role} completed')
        return {'analysis': analysis}

def create_agents():
    return {
        'token_fundamentals_analyst': MockAgent('Token Fundamentals Analyst', 'fundamentals analysis'),
        'liquidity_analyst': MockAgent('Liquidity Analyst', 'liquidity analysis'),
        'bull_researcher': MockAgent('Bull Researcher', 'bullish research'),
        'bear_researcher': MockAgent('Bear Researcher', 'bearish research'),
        'trader_agent': MockAgent('Trading Agent', 'trading strategy'),
        'portfolio_manager': MockAgent('Portfolio Manager', 'portfolio management'),
    }

def run_workflow(crypto_symbol):
    global workflow_state
    
    workflow_state['status'] = 'running'
    workflow_state['start_time'] = datetime.now()
    workflow_state['logs'] = []
    
    socketio.emit('workflow_start', {
        'symbol': crypto_symbol,
        'start_time': workflow_state['start_time'].isoformat()
    })
    
    agents = create_agents()
    results = {}
    
    try:
        # Stage 1: Analyst Team
        workflow_state['current_stage'] = 'analyst_team'
        socketio.emit('stage_update', {'stage': 'analyst_team', 'status': 'running'})
        
        fundamentals_result = agents['token_fundamentals_analyst'].analyze(crypto_symbol)
        liquidity_result = agents['liquidity_analyst'].analyze(crypto_symbol)
        
        results['analyst_team'] = {
            'fundamentals': fundamentals_result.get('analysis', ''),
            'liquidity': liquidity_result.get('analysis', '')
        }
        
        socketio.emit('stage_complete', {'stage': 'analyst_team', 'results': results['analyst_team']})
        
        # Stage 2: Research Team
        workflow_state['current_stage'] = 'researcher_debate'
        socketio.emit('stage_update', {'stage': 'researcher_debate', 'status': 'running'})
        
        bull_result = agents['bull_researcher'].analyze(crypto_symbol)
        bear_result = agents['bear_researcher'].analyze(crypto_symbol)
        
        results['research_team'] = {
            'bull': bull_result.get('analysis', ''),
            'bear': bear_result.get('analysis', '')
        }
        
        socketio.emit('stage_complete', {'stage': 'researcher_debate', 'results': results['research_team']})
        
        # Stage 3: Trading Plan
        workflow_state['current_stage'] = 'trading_plan'
        socketio.emit('stage_update', {'stage': 'trading_plan', 'status': 'running'})
        
        trading_result = agents['trader_agent'].analyze(crypto_symbol)
        results['trading_plan'] = trading_result.get('analysis', '')
        
        socketio.emit('stage_complete', {'stage': 'trading_plan', 'results': results['trading_plan']})
        
        # Stage 4: Portfolio Management
        workflow_state['current_stage'] = 'portfolio_management'
        socketio.emit('stage_update', {'stage': 'portfolio_management', 'status': 'running'})
        
        pm_result = agents['portfolio_manager'].analyze(crypto_symbol)
        results['portfolio_management'] = pm_result.get('analysis', '')
        
        socketio.emit('stage_complete', {'stage': 'portfolio_management', 'results': results['portfolio_management']})
        
        # Workflow completion
        workflow_state['status'] = 'completed'
        workflow_state['results'] = results
        
        socketio.emit('workflow_complete', {
            'results': results,
            'duration': str(datetime.now() - workflow_state['start_time'])
        })
        
    except Exception as e:
        workflow_state['status'] = 'error'
        socketio.emit('workflow_error', {'error': str(e)})

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/dashboard')
def dashboard():
    return render_template('dashboard.html')

@app.route('/api/yasuo/7d')
def api_yasuo_7d():
    try:
        if not SUPABASE_KEY:
            return jsonify({"error": "Supabase key not configured"}), 500
        headers = {
            'apikey': SUPABASE_KEY,
            'Authorization': f'Bearer {SUPABASE_KEY}',
            'Content-Type': 'application/json'
        }
        url = f"{SUPABASE_URL}/rest/v1/yasuo_daily_analysis?select=*&order=analysis_date.desc&limit=7"
        with httpx.Client(timeout=15) as client:
            r = client.get(url, headers=headers)
            r.raise_for_status()
            data = r.json()
        # Return in chronological order (oldest -> newest)
        data = sorted(data, key=lambda x: x.get('analysis_date', ''))
        return jsonify({"status": "ok", "data": data})
    except Exception as e:
        return jsonify({"status": "error", "error": str(e)}), 500

@app.route('/favicon.ico')
def favicon():
    return '', 204

@app.route('/api/workflow/start', methods=['POST'])
def start_workflow():
    data = request.get_json()
    crypto_symbol = data.get('symbol', 'ETH')
    
    thread = threading.Thread(target=run_workflow, args=(crypto_symbol,))
    thread.daemon = True
    thread.start()
    
    return jsonify({'status': 'started', 'symbol': crypto_symbol})

@app.route('/api/workflow/status')
def workflow_status():
    return jsonify(workflow_state)

@socketio.on('connect')
def handle_connect():
    emit('connected', {'status': 'Connected to ETH Trading Framework (Demo mode)'})

@socketio.on('disconnect')
def handle_disconnect():
    print('Client disconnected')

if __name__ == '__main__':
    print("🚀 Starting ETH Trading Framework Web UI...")
    print("📊 Mode: Demo")
    port = int(os.getenv('PORT', '5000'))
    print(f"📊 Dashboard: http://localhost:{port}")
    print("💡 Tip: Mở browser và truy cập http://localhost:5000")
    print("🔧 Press Ctrl+C to stop server")
    
    try:
        socketio.run(app, debug=False, host='0.0.0.0', port=port)
    except KeyboardInterrupt:
        print("\n👋 Server stopped by user")
