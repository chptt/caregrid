@echo off
REM Comprehensive setup script for MediChain project

echo === MediChain Project Setup ===
echo.

REM Check Python version
echo Checking Python version...
python --version
if %ERRORLEVEL% NEQ 0 (
    echo Error: Python is not installed!
    echo Please install Python from https://www.python.org/
    exit /b 1
)

REM Check if Node.js is installed
echo.
echo Checking Node.js installation...
node --version
if %ERRORLEVEL% NEQ 0 (
    echo Error: Node.js is not installed!
    echo Please install Node.js from https://nodejs.org/
    exit /b 1
)

REM Install Python dependencies
echo.
echo Installing Python dependencies...
if exist requirements.txt (
    pip install -r requirements.txt
    if %ERRORLEVEL% EQU 0 (
        echo [SUCCESS] Python dependencies installed successfully
    ) else (
        echo [ERROR] Failed to install Python dependencies
        exit /b 1
    )
) else (
    echo Error: requirements.txt not found!
    exit /b 1
)

REM Install blockchain dependencies
echo.
echo Installing blockchain dependencies...
cd caregrid_chain
if exist package.json (
    call npm install
    if %ERRORLEVEL% EQU 0 (
        echo [SUCCESS] Blockchain dependencies installed successfully
    ) else (
        echo [ERROR] Failed to install blockchain dependencies
        exit /b 1
    )
) else (
    echo Error: package.json not found in caregrid_chain!
    exit /b 1
)
cd ..

REM Create necessary directories
echo.
echo Creating necessary directories...
if not exist logs mkdir logs
if not exist caregrid_chain\deployments mkdir caregrid_chain\deployments
echo [SUCCESS] Directories created

REM Run Django migrations
echo.
echo Running Django migrations...
python manage.py makemigrations
python manage.py migrate
if %ERRORLEVEL% EQU 0 (
    echo [SUCCESS] Database migrations completed
) else (
    echo [ERROR] Database migrations failed
    exit /b 1
)

echo.
echo === Setup Complete ===
echo.
echo Next steps:
echo 1. Install and start Redis (download from https://redis.io/download)
echo 2. Start blockchain: scripts\start-blockchain.bat
echo 3. Update contract addresses: python scripts\update_contract_addresses.py
echo 4. Start Django server: python manage.py runserver
echo.
