@echo off
REM AgroSky Insight - Quick Start Script for Windows

echo Starting AgroSky Insight...
echo.

REM Check if Docker is installed
docker-compose --version >nul 2>&1
if %errorlevel% == 0 (
    echo Docker Compose found
    echo.
    echo Starting with Docker Compose...
    docker-compose up --build
) else (
    echo Docker Compose not found. Starting manually...
    echo.
    
    REM Start backend in new window
    echo Starting Backend...
    start "AgroSky Backend" cmd /k "cd backend && python -m venv venv && venv\Scripts\activate && pip install -r requirements.txt && python main.py"
    
    REM Wait a bit for backend to start
    timeout /t 5 /nobreak >nul
    
    REM Start frontend in new window
    echo Starting Frontend...
    start "AgroSky Frontend" cmd /k "cd frontend && npm install && npm run dev"
    
    echo.
    echo AgroSky Insight is starting...
    echo.
    echo Frontend: http://localhost:3000
    echo Backend API: http://localhost:8000
    echo API Docs: http://localhost:8000/docs
    echo.
    echo Check the opened windows for status.
)

pause


