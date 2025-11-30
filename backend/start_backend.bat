@echo off
cd /d %~dp0
call venv\Scripts\activate.bat
echo.
echo ========================================
echo  ЗАПУСК BACKEND СЕРВЕРА
echo ========================================
echo.
python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload
pause


