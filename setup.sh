#!/bin/bash
# Quick setup script for Fantasy Football Injury Tracker

set -e

echo "=================================="
echo "Fantasy Football Injury Tracker"
echo "Setup Script"
echo "=================================="
echo ""

# Check Python version
echo "Checking Python version..."
python_version=$(python3 --version 2>&1 | awk '{print $2}')
echo "✓ Python $python_version detected"
echo ""

# Install dependencies
echo "Installing dependencies..."
pip3 install -r requirements.txt
echo "✓ Dependencies installed"
echo ""

# Create .env if it doesn't exist
if [ ! -f .env ]; then
    echo "Creating .env file from template..."
    cp .env.example .env
    echo "✓ .env file created"
    echo ""
    echo "⚠️  IMPORTANT: You need to edit .env and add your credentials:"
    echo "   1. Yahoo Client ID and Secret"
    echo "   2. Your Yahoo League ID"
    echo ""
    echo "Run: nano .env"
    echo "     (or use your preferred text editor)"
else
    echo "✓ .env file already exists"
fi

echo ""
echo "=================================="
echo "Setup Complete!"
echo "=================================="
echo ""
echo "Next steps:"
echo "1. Edit .env with your Yahoo API credentials"
echo "2. Run: python3 monitor.py --once"
echo "   (This will authenticate with Yahoo)"
echo "3. Run: python3 monitor.py"
echo "   (Start continuous monitoring)"
echo ""
echo "For help: python3 monitor.py --help"
echo ""
