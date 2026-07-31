@echo off
echo ===================================================
echo   Starting Placement Portal (Backend + Frontend)   
echo ===================================================
echo.

:: Start Backend
echo [1/2] Starting Flask Backend...
start "Placement Portal Backend" cmd /k "cd backend && .venv\Scripts\python run.py"

:: Start Frontend
echo [2/2] Starting React/Vite Frontend...
start "Placement Portal Frontend" cmd /k "cd frontend && npm run dev"

echo.
echo ===================================================
echo   Both services are now starting in separate windows.
echo   - Backend runs on http://127.0.0.1:5000
echo   - Frontend will open in your browser
echo ===================================================
pause
