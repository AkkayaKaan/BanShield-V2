@echo off
setlocal EnableDelayedExpansion

echo [INFO] BanShield Installation Script for Windows
echo [INFO] Checking for Node.js and Python...

:: Check for Node.js
where node >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo [ERROR] Node.js is not installed! Please install Node.js from https://nodejs.org/
    pause
    exit /b 1
)

:: Check for Python
where python >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo [ERROR] Python is not installed! Please install Python from https://www.python.org/
    pause
    exit /b 1
)

:: Check Python version (needs to be 3.x)
python --version | findstr /R "Python 3\." >nul
if %ERRORLEVEL% neq 0 (
    echo [ERROR] Python 3 is required! Please install Python 3 from https://www.python.org/
    pause
    exit /b 1
)

echo [INFO] Installing Node.js dependencies...
call npm install steam-user steam-tradeoffer-manager steam-totp steamcommunity dotenv
if %ERRORLEVEL% neq 0 (
    echo [ERROR] Failed to install Node.js dependencies!
    pause
    exit /b 1
)

echo [INFO] Installing Python dependencies...
python -m pip install --upgrade pip
python -m pip install requests beautifulsoup4 python-dotenv PyQt5 psutil
if %ERRORLEVEL% neq 0 (
    echo [ERROR] Failed to install Python dependencies!
    pause
    exit /b 1
)

echo [INFO] Creating .env file if it does not exist...
if not exist .env (
    echo ProfileToWatch= >> .env
    echo WatchingProfileUsername= >> .env
    echo WatchingProfilePassword= >> .env
    echo WatchingProfileSharedSecret= >> .env
    echo WatchingProfileIdentitySecret= >> .env
    echo BankAccountTradeURL= >> .env
    echo BankAccountUsername= >> .env
    echo BankAccountPassword= >> .env
    echo BankAccountSharedSecret= >> .env
    echo AutoAccept=true >> .env
    echo INVENTORY_TYPE=cs2 >> .env
    echo TELEGRAM_BOT_TOKEN= >> .env
    echo TELEGRAM_CHAT_ID= >> .env
    echo TelegramNotify=true >> .env
    echo CHECK_INTERVAL=20 >> .env
    echo AUTO_RESTART=true >> .env
    echo SCHEDULED_RESTART=false >> .env
    echo [INFO] .env file created. Please fill in the required values.
) else (
    echo [INFO] .env file already exists.
)

echo [INFO] Installation completed successfully!
echo [INFO] Please ensure you have filled in the .env file with your Steam and Telegram credentials.
pause
exit /b 0
