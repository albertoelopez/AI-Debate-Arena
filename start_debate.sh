#!/bin/bash
# AI Debate Arena Launcher

echo "🎭 Starting AI Debate Arena..."
echo "=========================="

# Check if required dependencies are installed
echo "📦 Checking dependencies..."
python -c "import aiohttp, dotenv; print('✅ Core dependencies OK')" 2>/dev/null || {
    echo "❌ Missing dependencies. Installing..."
    pip install aiohttp python-dotenv
}

# Check if Ollama is running (fallback option)
if curl -s http://localhost:11434/api/tags >/dev/null 2>&1; then
    echo "✅ Ollama server detected (fallback LLM)"
else
    echo "⚠️  Ollama not running (using API keys only)"
fi

# Check API keys
if grep -q "GROQ_API_KEY=gsk_" .env 2>/dev/null; then
    echo "✅ Groq API key configured"
elif grep -q "GOOGLE_API_KEY=AIza" .env 2>/dev/null; then
    echo "✅ Google API key configured"
else
    echo "⚠️  No API keys found - will use Ollama fallback"
fi

echo ""
echo "🚀 Launching debate arena..."
echo "   Server: http://localhost:8080"
echo "   Press Ctrl+C to stop"
echo ""

# Start the server
python main.py