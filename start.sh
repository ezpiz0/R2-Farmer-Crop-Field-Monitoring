#!/bin/bash

# AgroSky Insight - Quick Start Script
# This script starts both backend and frontend in development mode

echo "🛰️  Starting AgroSky Insight..."
echo ""

# Check if Docker is installed
if command -v docker-compose &> /dev/null; then
    echo "✅ Docker Compose found"
    echo ""
    echo "Starting with Docker Compose..."
    docker-compose up --build
else
    echo "⚠️  Docker Compose not found. Starting manually..."
    echo ""
    
    # Start backend
    echo "🔧 Starting Backend..."
    cd backend
    
    if [ ! -d "venv" ]; then
        echo "Creating virtual environment..."
        python -m venv venv
    fi
    
    source venv/bin/activate
    pip install -r requirements.txt
    python main.py &
    BACKEND_PID=$!
    cd ..
    
    # Start frontend
    echo "🎨 Starting Frontend..."
    cd frontend
    
    if [ ! -d "node_modules" ]; then
        echo "Installing dependencies..."
        npm install
    fi
    
    npm run dev &
    FRONTEND_PID=$!
    cd ..
    
    echo ""
    echo "✅ AgroSky Insight is running!"
    echo ""
    echo "📱 Frontend: http://localhost:3000"
    echo "🔧 Backend API: http://localhost:8000"
    echo "📚 API Docs: http://localhost:8000/docs"
    echo ""
    echo "Press Ctrl+C to stop..."
    
    # Wait for both processes
    wait $BACKEND_PID $FRONTEND_PID
fi


