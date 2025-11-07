#!/bin/bash

echo "🚀 Starting SportSync AI - Triple Intelligence System"
echo "=================================================="
echo ""

# Check if .env exists
if [ ! -f .env ]; then
    echo "❌ Error: .env file not found!"
    echo "Please create .env file with your OPENAI_API_KEY"
    exit 1
fi

# Load environment
export $(cat .env | grep -v '^#' | xargs)

# Check OpenAI key
if [ -z "$OPENAI_API_KEY" ]; then
    echo "❌ Error: OPENAI_API_KEY not found in .env!"
    exit 1
fi

echo "✅ Environment loaded"
echo "✅ OpenAI API Key found: ${OPENAI_API_KEY:0:20}..."
echo ""

# Install dependencies if needed
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
    source venv/bin/activate
    echo "📦 Installing dependencies..."
    pip install -r requirements.txt
else
    source venv/bin/activate
fi

echo ""
echo "🎯 Launching Streamlit app..."
echo "=================================================="
echo ""

streamlit run app_v2.py --server.port=8501 --server.address=0.0.0.0
