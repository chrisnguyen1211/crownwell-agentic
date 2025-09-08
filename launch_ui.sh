#!/bin/bash

echo "🚀 ETH Trading Framework - Web UI Launcher"
echo "=========================================="

# Check if we're in the right directory
if [ ! -d "web_ui" ]; then
    echo "❌ Error: web_ui directory not found"
    echo "Please run this script from the project root directory"
    exit 1
fi

# Navigate to web_ui directory
cd web_ui

# Check if virtual environment exists
if [ ! -d "ui_venv" ]; then
    echo "❌ Error: ui_venv not found"
    echo "Creating virtual environment..."
    python3 -m venv ui_venv
    source ui_venv/bin/activate
    pip install Flask Flask-SocketIO python-dotenv python-socketio eventlet
else
    echo "✅ Virtual environment found"
fi

# Check if app.py exists
if [ ! -f "app.py" ]; then
    echo "❌ Error: app.py not found in web_ui directory"
    exit 1
fi

# Activate virtual environment and run server
echo "🔧 Activating virtual environment..."
source ui_venv/bin/activate

echo "🚀 Starting ETH Trading Framework Web UI..."
echo "📊 Dashboard will be available at: http://localhost:5000"
echo "💡 Press Ctrl+C to stop the server"
echo ""

# Run the application
python app.py
