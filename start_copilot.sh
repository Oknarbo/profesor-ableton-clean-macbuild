#!/bin/bash
# 🎸 Profesor Ableton - Linux/Mac Launcher 🎵

echo "🎸 Starting Profesor Ableton..."

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "❌ Virtual environment not found! Run setup.py first:"
    echo "   python setup.py"
    exit 1
fi

# Activate virtual environment
source venv/bin/activate

# Check if .env exists
if [ ! -f ".env" ]; then
    echo "❌ .env file not found! Copy from env_example.txt and add your API key"
    exit 1
fi

echo "🎵 Launching server and GUI..."

# Start server in background
python copilot_server.py &
SERVER_PID=$!

# Wait a moment for server to start
sleep 2

# Start GUI
python gui_copilot.py

# Cleanup: kill server when GUI closes
echo "🎸 Cleaning up..."
kill $SERVER_PID 2>/dev/null

echo "🎵 Groovy session complete! Far out!"
