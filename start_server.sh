#!/bin/bash

# Start PredictionZ Backend Server

echo "🔮 Starting PredictionZ Backend..."

# Activate virtual environment
source venv/bin/activate

# Check if .env exists
if [ ! -f .env ]; then
    echo "❌ Error: .env file not found!"
    echo "Please create .env with your ANTHROPIC_API_KEY"
    exit 1
fi

# Check if ANTHROPIC_API_KEY is set
if grep -q "your_key_here" .env; then
    echo "⚠️  Warning: Please update ANTHROPIC_API_KEY in .env file"
fi

# Start server
echo "✅ Starting FastAPI server on http://localhost:8000"
echo "📖 API Docs: http://localhost:8000/docs"
echo ""
python app.py
