@echo off
echo Starting ThreatModelerX...

echo Starting backend server...
cd backend
start cmd /k "python -m venv venv && venv\Scripts\activate && pip install -r requirements.txt && uvicorn app.main:app --reload --host 0.0.0.0 --port 8000"

cd ..
echo Waiting for backend to start...
timeout /t 5 /nobreak > nul

echo Starting frontend server...
start cmd /k "npm run dev"

echo.
echo ========================================
echo   ThreatModelerX is starting...
echo ========================================
echo.
echo Backend:  http://localhost:8000
echo Frontend: http://localhost:5173
echo API Docs: http://localhost:8000/docs
echo.
echo Press any key to open the application...
pause > nul
start http://localhost:5173