@echo off
echo Starting DevSecOps Automation Project...

echo Starting backend server...
cd backend
call .venv\Scripts\activate.bat
start cmd /k "uvicorn app.main:app --reload --host 0.0.0.0 --port 8000"

cd ..
echo Starting frontend server...
start cmd /k "npm run dev"

echo Application started!
echo Backend: http://localhost:8000
echo Frontend: http://localhost:5173
echo.
echo Press any key to open the application in your browser...
pause > nul
start http://localhost:5173