#!/bin/bash

# F&O Dashboard Backend - Quick Start Script

echo "🚀 F&O Dashboard Backend - Quick Start"
echo "======================================"
echo ""

# Check Python version
echo "📋 Checking Python version..."
python3 --version

# Create virtual environment
echo ""
echo "📦 Creating virtual environment..."
python3 -m venv venv

# Activate virtual environment
echo ""
echo "✅ Activating virtual environment..."
source venv/bin/activate

# Install dependencies
echo ""
echo "📥 Installing dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

# Create .env if not exists
if [ ! -f .env ]; then
    echo ""
    echo "📝 Creating .env file..."
    cp .env.example .env
    echo "⚠️  Please edit .env and add your ANGEL_API_KEY"
fi

echo ""
echo "✅ Setup complete!"
echo ""
echo "Next steps:"
echo "1. Edit .env and add your ANGEL_API_KEY"
echo "2. Start Redis: docker run -d -p 6379:6379 redis"
echo "3. Run backend: uvicorn app.main:app --reload"
echo "4. Visit: http://localhost:8000/docs"
echo ""
