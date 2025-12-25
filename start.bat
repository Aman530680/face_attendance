@echo off
echo ========================================
echo   FACE RECOGNITION ATTENDANCE SYSTEM
echo ========================================
echo.

echo [1/4] Checking Python installation...
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python 3.7+ from https://python.org
    pause
    exit /b 1
)
echo ✓ Python found

echo.
echo [2/4] Checking MySQL connection...
mysql -u root -p%MYSQL_PASSWORD% -e "SELECT 1;" >nul 2>&1
if errorlevel 1 (
    echo WARNING: MySQL connection test failed
    echo Make sure MySQL is running and password is correct in config.py
)
echo ✓ MySQL check complete

echo.
echo [3/4] Installing dependencies...
pip install -r requirements.txt
if errorlevel 1 (
    echo ERROR: Failed to install dependencies
    pause
    exit /b 1
)
echo ✓ Dependencies installed

echo.
echo [4/4] Starting Face Recognition Attendance System...
echo.
echo Opening in browser: http://localhost:5000
echo Press Ctrl+C to stop the server
echo.

start http://localhost:5000
python app.py

pause