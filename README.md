# BanShield-V2.0.2

# Last Update: 05.08.2025
Fixed:
Items were being sent to the backup account even when the account was not banned. This issue is now resolved.

Added multi-check ban detection:
Instead of triggering item transfers on a single ban detection, the bot now checks for a ban 10 times in a row (with short delays).

False positive prevention:
The item transfer process is only triggered if at least 2 out of 10 checks detect a ban.
This prevents items from being transferred due to one-off web errors or Steam page issues.



BanShield-V2 is an advanced, automated tool designed to monitor Steam profiles for VAC (Valve Anti-Cheat) or game bans and protect in-game inventories by transferring items to a designated backup account upon ban detection. The project integrates a Python-based ban monitoring system with a modern PyQt5 GUI and Node.js scripts for seamless Steam trade operations. Optimized for both Windows and Linux, it is launched via an intuitive graphical interface and includes enhanced features for user convenience and reliability.

## Purpose

When a Steam account receives a VAC or game ban, its inventory becomes locked, preventing trading or transferring items. Steam's ban detection and inventory lock process typically takes **40 minutes to 1 hour**, providing a critical window to safeguard valuable items. BanShield-V2 leverages this window by continuously monitoring a specified Steam profile for bans. Upon detection, it automatically initiates a trade to transfer all tradable items (from games like Counter-Strike 2, Team Fortress 2, Dota 2, and Steam collectibles) to a secure backup account, ensuring your inventory is preserved.

BanShield-V2 aims to provide Steam users with peace of mind through automation, eliminating the need for manual intervention during a ban event, with a user-friendly interface and robust error handling.

## Features

- **Real-Time Ban Monitoring**: Continuously checks a specified Steam profile for VAC or game bans at configurable intervals (20 to 300 seconds, default: 20 seconds).
- **Automated Trade Execution**: Instantly initiates a trade to transfer all tradable items to a backup account upon ban detection using Steam's trade system.
- **Modern PyQt5 GUI**: A sleek, dark-themed interface (updated to a professional dark aesthetic with gradient buttons and improved typography) for easy configuration, real-time log monitoring, and status updates.
- **Telegram Notifications**: Sends real-time alerts to a Telegram chat for ban detection and monitoring status, with automatic deletion of previous messages to keep the chat clean.
- **Automatic Trade Acceptance**: Optional `AutoAccept` feature for the backup account to streamline trade acceptance without manual intervention.
- **Multi-Game Inventory Support**: Supports transferring items from multiple Steam games, including Counter-Strike 2, Team Fortress 2, Dota 2, and Steam collectibles, with configurable inventory selection.
- **WatchDog System**: A dedicated `WatchDog.js` script monitors incoming trade offers and ensures timely trade acceptance, with fallback mechanisms to relaunch trade scripts if needed.
- **Secure Configuration**: Stores sensitive information (e.g., Steam credentials, trade URLs, Telegram tokens) in a `.env` file, editable via the GUI for ease and security.
- **Error Handling and Fullscreen Alerts**: Displays fullscreen error messages for critical failures (e.g., session errors, trade rejections) on Windows and Linux, with a 30-second timeout before script termination.
- **Customizable Check Intervals**: Adjustable via a slider in the GUI, allowing users to balance monitoring frequency and system load (20–300 seconds).
- **Inventory Type Selection**: GUI-based selection of specific game inventories (CS2, TF2, Dota 2, or all) to transfer, with an "All Inventory" option for simplicity.
- **Robust Trade Confirmation**: Uses unique, randomly generated trade keys to ensure secure and correct trade matching, with retry mechanisms for mobile confirmations.
- **Windows and Linux Optimized**: Designed for both Windows and Linux with platform-specific scripts for easy setup.
- **RAM Usage Display**: Displays the total RAM usage of BanShield-V2 in the GUI for performance monitoring.
- **Auto Restart on Crash**: Automatically restarts the application if a crash is detected, ensuring continuous operation.
- **Timed Auto Restart**: When enabled, the bot restarts every 2 hours to maintain stability and performance.
- **Clear Log Button**: A button in the GUI that clears all displayed logs for a clean interface.

## How It Works

1. **Ban Monitoring**:

   - `BanChecker.py` periodically scrapes the specified Steam profile using `requests` and `BeautifulSoup` to detect phrases like "VAC Ban on record" or "Game Ban on record."
   - Configurable check intervals (20–300 seconds) via the GUI slider.

2. **Ban Detection**:

   - Upon detecting a ban, `BanChecker.py` sends a Telegram notification (if enabled) and triggers `SendTrade.js` to initiate a trade offer with all tradable items.
   - The system logs the event in the GUI with a color-coded alert and emits a system beep.

3. **Trade Execution**:

   - `SendTrade.js` logs into the monitored Steam account, gathers tradable items from selected inventories (CS2, TF2, Dota 2, or all), and sends a trade offer to the backup account with a unique trade key.
   - If `AutoAccept` is enabled, `AutoAccept.js` runs on the backup account to automatically accept the trade by matching the trade key.
   - `WatchDog.js` monitors incoming trade offers, ensures timely acceptance, and relaunches trade scripts (`SendTrade.js` or `AutoAccept.js`) if no trade is detected within 5 minutes.

4. **GUI Interface**:

   - `BanShieldGUI.py` provides a modern, dark-themed interface with a collapsible settings panel (toggled via a ☰ button) for configuring the `.env` file, starting/stopping the bot, and viewing logs.
   - Logs are color-coded (e.g., green for "No Ban," red for errors, yellow for alerts) and include timestamps for clarity.
   - Status updates (e.g., "No Ban," "Ban Detected!") are displayed prominently with color-coded indicators.
   - A RAM usage display shows the current memory consumption of the application.
   - A "Clear Log" button allows users to reset the log display in the GUI.
   - Auto-restart features (crash recovery and timed restarts) ensure continuous operation.

5. **Telegram Integration**:

   - `TelegramInformer.py` sends real-time status updates to a Telegram chat, replacing the previous message to avoid clutter.
   - A reset function clears the last 15 messages in the Telegram channel to maintain a clean log.

6. **Security**:

   - Trade offers include a 14-character random key to ensure secure matching.
   - Sensitive data is stored in the `.env` file, editable via the GUI to minimize errors.
   - Fullscreen error displays (via `WatchDog.js`) alert users to critical issues like session failures or trade rejections.

## Prerequisites

- **Windows or Linux Operating System**: Optimized and tested for both Windows and Linux environments.
- **Python 3.8+**: Required for `BanChecker.py`, `TelegramInformer.py`, and `BanShieldGUI.py`.
- **Node.js 14+**: Required for `SendTrade.js`, `AutoAccept.js`, and `WatchDog.js`.
- **Steam Account Credentials**: For both the monitored and backup accounts, including:
  - Username
  - Password
  - Shared Secret (for 2FA)
  - Identity Secret (for trade confirmations)
  - Trade URL (for the backup account)
- **Steam Mobile/Desktop Authenticator**: Enabled on both accounts for two-factor authentication.
- **Telegram Bot (Optional)**: For notifications, requires a Telegram Bot Token and Chat ID.
- **Internet Connection**: Necessary for Steam API interactions and profile scraping.

## Installation

1. **Clone the Repository**:

   ```bash
   git clone https://github.com/AkkayaKaan/BanShield-V2
   cd BanShield-V2
   ```

2. **Install Dependencies**:

   - For **Windows**, run `install.bat` to install all required dependencies:

     ```bash
     install.bat
     ```
   - For **Linux**, run `install.sh` to install all required dependencies:

     ```bash
     chmod +x install.sh
     ./install.sh
     ```
   - These scripts install Python dependencies (`PyQt5`, `requests`, `beautifulsoup4`, `python-dotenv`) and Node.js dependencies (`steam-user`, `steamcommunity`, `steam-tradeoffer-manager`, `steam-totp`, `dotenv`).

3. **Configure the** `.env` **File**:

   - Launch the GUI with `Start.bat` (Windows) or `start.sh` (Linux) and use the settings panel to configure the `.env` file (recommended).
   - Alternatively, manually create/edit the `.env` file with the following template:

     ```plaintext
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
     INVENTORY_TYPE=cs2,tf2,dota2
     CHECK_INTERVAL=20
     AUTO_RESTART_ON_CRASH=true
     TIMED_AUTO_RESTART=true
     ```
   - Ensure `ProfileToWatch` is the public Steam profile URL of the monitored account.
   - Obtain `SharedSecret` and `IdentitySecret` from your Steam Mobile Authenticator (e.g., via Steam Desktop Authenticator).
   - Set `AutoAccept=true` for automatic trade acceptance.
   - Configure `TELEGRAM_BOT_TOKEN` and `TELEGRAM_CHAT_ID` for Telegram notifications.
   - Specify `INVENTORY_TYPE` (e.g., `cs2`, `tf2`, `dota2`, `all`, or a comma-separated combination).
   - Set `CHECK_INTERVAL` (20–300 seconds) for ban check frequency.
   - Set `AUTO_RESTART_ON_CRASH=true` to enable automatic restart on crashes.
   - Set `TIMED_AUTO_RESTART=true` to enable automatic restarts every 2 hours.

4. **Run the Application**:

   - For **Windows**, launch the GUI using `Start.bat`:

     ```bash
     Start.bat
     ```
   - For **Linux**, launch the GUI using `start.sh`:

     ```bash
     chmod +x start.sh
     ./start.sh
     ```

## Usage

1. **Launch the GUI**:

   - Run `Start.bat` (Windows) or `start.sh` (Linux) to open the BanShield-V2 interface with the updated dark theme.

2. **Configure Settings**:

   - Click the ☰ button to toggle the settings panel.
   - Enter or verify configuration details (Steam credentials, Telegram settings, inventory types, check interval, auto-restart options) in the GUI.
   - Use the inventory checkboxes to select which game inventories to transfer (CS2, TF2, Dota 2, or all).
   - Adjust the check interval using the slider (20–300 seconds).
   - Enable `Auto Restart on Crash` and `Timed Auto Restart` as needed.
   - Click "Save Config" to update the `.env` file. The GUI ensures all required fields are valid.

3. **Start the Bot**:

   - Click "Start Bot" to begin monitoring the specified Steam profile.
   - View real-time logs in the GUI (color-coded for errors, checks, and alerts), status updates (e.g., "No Ban," "Ban Detected!"), and RAM usage.
   - Click the "Clear Log" button to reset the log display if needed.
   - The "Last Check" field displays the timestamp of the latest profile check.
   - Telegram notifications (if enabled) provide updates on ban status.

4. **Stop the Bot**:

   - Click "Stop Bot" to halt monitoring and terminate all processes.

5. **Ban Detection and Trade**:

   - Upon ban detection:
     - The GUI displays a red "Ban Detected!" status, emits a system beep, and shows an alert.
     - A Telegram notification is sent (if enabled).
     - `SendTrade.js` initiates a trade with all tradable items to the backup account.
     - `WatchDog.js` monitors the trade and relaunches scripts if needed.
     - If `AutoAccept` is enabled, `AutoAccept.js` accepts the trade automatically.
   - The system exits cleanly after a successful trade or displays a fullscreen error for failures.
   - Auto-restart features ensure the bot resumes operation after crashes or scheduled restarts.

## File Structure

- `BanShieldGUI.py`: Main PyQt5 GUI script for configuration, monitoring, log display, RAM usage, and log clearing with a modern dark theme.
- `BanChecker.py`: Python script for monitoring Steam profiles for bans and triggering trade scripts.
- `SendTrade.js`: Node.js script for creating and sending trade offers with all tradable items.
- `AutoAccept.js`: Node.js script for automatically accepting trades on the backup account using a trade key.
- `WatchDog.js`: Node.js script for monitoring trade offers and ensuring timely acceptance with fallback mechanisms.
- `TelegramInformer.py`: Python script for sending Telegram notifications and managing chat messages.
- `.env`: Configuration file for sensitive information, preferably edited via the GUI.
- `install.bat` (Windows): Batch file for installing dependencies on Windows.
- `install.sh` (Linux): Shell script for installing dependencies on Linux.
- `Start.bat` (Windows): Batch file for launching the GUI on Windows.
- `start.sh` (Linux): Shell script for launching the GUI on Linux.

## Troubleshooting

- **Error: "ProfileToWatch is required!"**
  - Ensure `ProfileToWatch` is set to a valid Steam profile URL in the GUI or `.env` file.
- **Error: "TradeOfferManager session error"**
  - Verify Steam credentials and 2FA secrets in the GUI or `.env` file.
  - Ensure the Steam Mobile Authenticator is active and time-synchronized.
- **Trade Fails**
  - Confirm the backup account's trade URL is valid and both accounts have 2FA enabled.
  - Check for Steam Guard restrictions (e.g., new device login delays).
- **GUI Not Responding**
  - Run `install.bat` (Windows) or `install.sh` (Linux) to ensure all dependencies are installed.
  - Verify Python 3.8+ and Node.js 14+ are installed.
- **Telegram Notifications Not Working**
  - Ensure `TELEGRAM_BOT_TOKEN` and `TELEGRAM_CHAT_ID` are correctly configured in the GUI or `.env` file.
  - Check your internet connection and Telegram bot permissions.
- **Auto-Restart Not Working**
  - Verify `AUTO_RESTART_ON_CRASH` and `TIMED_AUTO_RESTART` are set to `true` in the `.env` file or GUI.
  - Check system permissions to ensure the application can restart itself on Windows or Linux.

## Security Considerations

- **Sensitive Information**: Never share the `.env` file or include it in version control. Use the GUI to edit it securely.
- **Steam Guard**: Both accounts must have Steam Mobile Authenticator enabled to avoid trade restrictions.
- **Backup Account**: Use a trusted backup account, as it will receive all transferred items.
- **Network Security**: Run BanShield-V2 on a secure network to protect Steam API requests.
- **Telegram Security**: Ensure your Telegram bot token and chat ID are kept private.

## Contributing

Contributions are welcome! To contribute:

1. Fork the repository.
2. Create a new branch (`git checkout -b feature/your-feature`).
3. Make changes and commit (`git commit -m "Add your feature"`).
4. Push to the branch (`git push origin feature/your-feature`).
5. Open a pull request with a detailed description of your changes.

## License

This project is licensed under the MIT License. See the LICENSE file for details.

## Acknowledgments

- Created by **Kaan Akkaya**.
- Built using PyQt5, BeautifulSoup, steam-user, and other open-source libraries.
- Special thanks to the community for feedback and contributions.

## Disclaimer

This tool is provided for educational and personal use only. The author is not responsible for any misuse, account bans, or loss of items resulting from its use. Ensure compliance with Steam's Terms of Service and use at your own risk.
