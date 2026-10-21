@echo off
cd /d "%~dp0"

start "Backend" cmd /k "venv\Scripts\activate && uvicorn backend.main:app --reload"
start "Giao dien" cmd /k "cd frontend && python -m http.server 5500"
start "Thiet bi IoT" cmd /k "venv\Scripts\activate && python iot\thiet_bi.py"

timeout /t 4 >nul
start http://127.0.0.1:5500