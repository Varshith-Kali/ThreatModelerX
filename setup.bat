@echo off
echo Setting up DevSecOps Automation Project...

echo Installing backend dependencies...
cd backend
python -m venv .venv
call .venv\Scripts\activate.bat
pip install -r requirements.txt

REM Install additional tools needed for scanning
pip install semgrep bandit

cd ..
echo Installing frontend dependencies...
npm install

echo Setup complete! Run start.bat to start the application.