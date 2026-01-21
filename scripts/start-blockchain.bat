@echo off
REM Script to start local Hardhat blockchain and deploy contracts

echo === Starting MediChain Blockchain Setup ===

REM Navigate to blockchain directory
cd caregrid_chain

REM Check if node_modules exists
if not exist "node_modules" (
    echo Installing blockchain dependencies...
    call npm install
)

REM Start Hardhat node in background
echo Starting Hardhat local blockchain...
start /B npx hardhat node > ..\logs\hardhat.log 2>&1

REM Wait for Hardhat to be ready
echo Waiting for Hardhat to be ready...
timeout /t 5 /nobreak > nul

REM Deploy contracts
echo Deploying smart contracts...
call npx hardhat run scripts/deploy-all.ts --network localhost

if %ERRORLEVEL% EQU 0 (
    echo [SUCCESS] Contracts deployed successfully!
    echo [SUCCESS] Hardhat node is running on http://127.0.0.1:8545
    echo [SUCCESS] Deployment info saved to caregrid_chain/deployments/
    echo.
    echo To stop the blockchain, use Task Manager to end the node.exe process
) else (
    echo [ERROR] Contract deployment failed!
    taskkill /F /IM node.exe
    exit /b 1
)

cd ..
