@echo off
echo ===================================================
echo Starting Centralized Log Error Counter Backend API
echo ===================================================
cd backend
python -m uvicorn main:app --reload --port 8000
pause
