#!/bin/bash

echo "[INFO] BanShield Installation Script for Linux/MacOS"

# Check for Node.js
if ! command -v node &> /dev/null; then
    echo "[ERROR] Node.js is not installed! Please install Node.js from https://nodejs.org/"
    exit 1
fi

# Check for Python
if ! command -v python3 &> /dev/null; then
    echo "[ERROR] Python3 is not installed! Please install Python3 from https://www.python.org/"
    exit 1
fi

# Check Python version (needs to be 3.x)
python_version=$(python3 --version 2>&1 | grep -o "Python 3\.")
if [ -z "$python_version" ]; then
    echo "[ERROR] Python 3 is required! Please install Python 3 from https://www.python.org/"
    exit 1
fi

echo "[INFO] Installing Node.js dependencies..."
npm install steam-user steam-tradeoffer-manager steam-totp steamcommunity dotenv
if [ $? -ne 0 ]; then
    echo "[ERROR] Failed to install Node.js dependencies!"
    exit 1
fi

echo "[INFO] Installing Python dependencies..."
python3 -m pip install --upgrade pip
python3 -m pip install requests beautifulsoup4 python-dotenv PyQt5 psutil
if [ $? -ne 0 ]; then
    echo "[ERROR] Failed to install Python dependencies!"
    exit 1
fi

echo "[INFO] Creating .env file if it does not exist..."
if [ ! -f .env ]; then
    cat <<EOL > .env
ProfileToWatch=
WatchingProfileUsername=
WatchingProfilePassword=
WatchingProfileSharedSecret=
WatchingProfileIdentitySecret=
BankAccountTradeURL=
BankAccountUsername=
BankAccountPassword=
BankAccountSharedSecret=
AutoAccept=true
INVENTORY_TYPE=cs2
TELEGRAM_BOT_TOKEN=
TELEGRAM_CHAT_ID=
TelegramNotify=true
CHECK_INTERVAL=20
AUTO_RESTART=true
SCHEDULED_RESTART=false
EOL
    echo "[INFO] .env file created. Please fill in the required values."
else
    echo "[INFO] .env file already exists."
fi

echo "[INFO] Installation completed successfully!"
echo "[INFO] Please ensure you have filled in the .env file with your Steam and Telegram credentials."
exit 0
