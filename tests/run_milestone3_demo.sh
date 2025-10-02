#!/bin/bash
"""
Quick Demo Launcher for Milestone 3
===================================

This script provides quick access to different demo modes.
"""

echo "🎭 AI Guard Agent - Milestone 3 Demo Launcher"
echo "=============================================="
echo
echo "Available demo modes:"
echo "1. 🎬 Quick Automated Demo (2-3 minutes)"
echo "2. 🎮 Interactive Demo (full control)"
echo "3. 🔊 Audio Test Only"
echo "4. 📊 Performance Test Only"
echo
echo "Recommendations:"
echo "- Use headphones or speakers for audio experience"
echo "- Ensure microphone access (not required for demo)"
echo "- For best experience, run in a quiet environment"
echo

# Check if Python environment is set up
if ! python -c "import sys; sys.path.append('src'); from dialogue import conversation_controller" 2>/dev/null; then
    echo "❌ Error: Required modules not found"
    echo "Please ensure you have:"
    echo "1. Installed all dependencies: pip install -r requirements.txt"
    echo "2. Run from the project root directory"
    exit 1
fi

echo "✅ System check passed"
echo

# Run the demo
echo "Starting Milestone 3 Demo..."
echo "Press Ctrl+C at any time to exit"
echo

python milestone3_demo.py