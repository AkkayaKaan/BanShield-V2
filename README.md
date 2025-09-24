# BanShield-V2

**BanShield-V2** is an advanced, automated tool designed to monitor a Steam profile for VAC (Valve Anti-Cheat) or game bans. Upon detection, it protects your in-game inventory by automatically transferring items to a designated backup account. The project combines a Python-based ban monitoring system with a user-friendly PyQt5 GUI and Node.js scripts for handling Steam trade operations.

---

## Purpose
When a Steam account receives a VAC or game ban, the inventory associated with that account becomes locked, preventing any further trading or transfer of items. However, Steam's ban detection and inventory lock process can take between **40 minutes to 1 hour**, providing a critical window to safeguard your items.

BanShield-V2 leverages this window by continuously monitoring a specified Steam profile for bans. Upon detecting a ban, it automatically initiates a trade to transfer all tradable items (from games like **Counter-Strike 2, Team Fortress 2, Dota 2, and Steam collectibles**) to a secure backup account, ensuring your valuable items are preserved.

---

## Features
- **Advanced Ban Detection**: Monitors profiles specifically for newly applied bans by looking for the *"0 day(s) since last ban"* status.
- **False-Positive Safeguard**: Performs multiple checks to confirm legitimacy before triggering transfers.
- **Automated Trade Execution**: Instantly initiates trades once a ban is confirmed.
- **User-Friendly GUI**: Modern PyQt5-based interface with real-time logs.
- **Dry-Run (Simulation) Mode**: Safely tests detection and transfer logic without sending real trades.
- **Telegram Notifications**: Sends real-time alerts to your mobile device.
- **Automatic Trade Acceptance**: AutoAccept.js script for automatic acceptance on the backup account.
- **Post-Trade Watchdog**: WatchDog.js ensures trades complete successfully.
- **Multi-Game Support**: Works with CS2 (730), TF2 (440), Dota 2 (570), and Steam collectibles (753).

---

## How It Works

### Advanced Monitoring
- `BanChecker.py` periodically scrapes the Steam profile using **requests** and **BeautifulSoup**.
- Detects the text *"0 day(s) since last ban"* to focus only on new bans.

### Ban Confirmation (Safeguard)
- The `multi_check_ban` function re-scans the profile multiple times.
- A ban must be verified across multiple checks before triggering trade.

### Trade Execution & Notification
- Once confirmed, `SendTrade.js` logs in and creates a trade offer.
- Telegram notifications are sent if configured.

### Trade Monitoring
- Trade sent to backup account via trade URL.
- `WatchDog.js` monitors the trade.
- `AutoAccept.js` accepts the trade on the backup account.

### Security
- Each trade includes a unique, random key in the trade message.

---

## Prerequisites
- **Operating System**: Windows, Linux, or macOS
- **Python**: 3.8+
- **Node.js**: 14+
- **Steam Account Credentials** (monitored + backup):
  - Username & Password
  - Shared Secret (2FA)
  - Identity Secret (trade confirmations)
  - Trade URL for backup account

---

## Installation

### Clone the Repository
```bash
git clone https://github.com/AkkayaKaan/BanShield-V2
cd BanShield-V2
```

### Install Dependencies
**Windows**
```
install.bat
```

**Linux/macOS**
```bash
# Python dependencies
pip install PyQt5 requests beautifulsoup4 python-dotenv psutil

# Node.js dependencies
npm install steam-user steamcommunity steam-tradeoffer-manager steam-totp dotenv
```

### Configure `.env`
You can configure using the GUI (**recommended**) or manually:
```ini
ProfileToWatch=https://steamcommunity.com/id/yourprofile
WatchingProfileUsername=your_steam_username
WatchingProfilePassword=your_steam_password
WatchingProfileSharedSecret=your_2fa_shared_secret
WatchingProfileIdentitySecret=your_2fa_identity_secret
BankAccountTradeURL=your_backup_account_trade_url
BankAccountUsername=your_backup_account_username
BankAccountPassword=your_backup_account_password
BankAccountSharedSecret=your_backup_account_2fa_shared_secret
AutoAccept=true
TELEGRAM_BOT_TOKEN=your_telegram_bot_token
TELEGRAM_CHAT_ID=your_telegram_chat_id
TelegramNotify=true
INVENTORY_TYPE=all
CHECK_INTERVAL=20
AUTO_RESTART=false
SCHEDULED_RESTART=false
```

---

## Usage
- **Launch GUI**: `Start.bat` (Windows) or `python3 BanShieldGUI.py` (Linux/macOS)
- **Configure Settings**: Enter details in the settings panel.
- **Dry-Run Test**: Verify setup without sending trades.
- **Start Bot**: Begin live monitoring.
- **Stop Bot**: Halt monitoring.

---

## File Structure
- **BanShieldGUI.py** → Main PyQt5 GUI script
- **BanChecker.py** → Monitors the Steam profile
- **SendTrade.js** → Creates and sends the trade offer
- **AutoAccept.js** → Accepts trades automatically
- **WatchDog.js** → Monitors trade status
- **TelegramInformer.py** → Sends Telegram notifications
- **.env** → Configuration file
- **install.bat / Start.bat** → Easy install & launch scripts

---

## Disclaimer
This tool is provided for **educational and personal use only**. The author is not responsible for any misuse, account bans, or loss of items resulting from use of this software. **Use at your own risk** and ensure compliance with Steam's Terms of Service.

