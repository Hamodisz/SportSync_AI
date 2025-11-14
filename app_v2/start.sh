#!/bin/bash

# SportSync AI v2 - Quick Start Script

echo "🚀 Starting SportSync AI v2..."
echo "================================"
echo ""

# Check if streamlit is installed
if ! command -v streamlit &> /dev/null; then
    echo "❌ Streamlit not found!"
    echo "Installing streamlit..."
    pip install streamlit
fi

echo "✅ Streamlit found"
echo ""
echo "🌐 Opening browser..."
echo "📍 URL: http://localhost:8501"
echo ""
echo "Press Ctrl+C to stop"
echo "================================"
echo ""

# Run the app
streamlit run main.py
