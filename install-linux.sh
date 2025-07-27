#!/bin/bash

echo "📦 BanShield-V2 Installer - Linux"

# Sanal ortam vs..
VENV_DIR="venv"

# Python ortamı
echo "🔧 Python venv oluşturuluyor..."
python3 -m venv $VENV_DIR
source $VENV_DIR/bin/activate

# Gerekli Python modülleri
echo "📥 Python modülleri yükleniyor..."
pip install --upgrade pip
pip install pyqt5 requests beautifulsoup4 python-dotenv

# Gerekli js modülleri
echo "📥 Node.js modülleri yükleniyor..."
npm install steam-user steamcommunity steam-tradeoffer-manager steam-totp dotenv

echo "✅ Kurulum tamamlandı. Artık start.sh ile başlatabilirsin."
