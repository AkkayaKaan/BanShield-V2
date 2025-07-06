# BanShield-V2

BanShield-V2 is an automated tool designed to monitor Steam profiles for VAC (Valve Anti-Cheat) or game bans and protect your in-game inventory by automatically transferring items to a designated backup account upon ban detection. The project combines a Python-based ban monitoring system with a user-friendly PyQt5 GUI and Node.js scripts for handling Steam trade operations. It is designed specifically for Windows users and is primarily launched through its graphical interface.

## Purpose

When a Steam account receives a VAC or game ban, the inventory associated with that account becomes locked, preventing any further trading or transfer of items. However, Steam's ban detection and inventory lock process can take between **40 minutes to 1 hour**, providing a critical window to safeguard your items. BanShield-V2 leverages this window by continuously monitoring a specified Steam profile for bans. Upon detecting a ban, it automatically initiates a trade to transfer all tradable items (from games like Counter-Strike 2, Team Fortress 2, Dota 2, and Steam collectibles) to a secure backup account, ensuring your valuable items are preserved.

The primary goal of BanShield-V2 is to provide peace of mind for Steam users by automating the process of inventory protection, eliminating the need for manual intervention during a stressful situation.

## Features

- **Real-Time Ban Monitoring**: Continuously checks a specified Steam profile for VAC or game bans at configurable intervals (default: 60 seconds).
- **Automated Trade Execution**: Upon ban detection, instantly initiates a trade to transfer all tradable items to a backup account using Steam's trade system.
- **User-Friendly GUI**: A modern PyQt5-based interface for easy configuration, monitoring, and real-time log/status updates.
- **Automatic Trade Acceptance**: Optional auto-accept feature for the backup account to streamline the trade process.
- **Multi-Game Support**: Supports inventory transfers for multiple Steam games, including Counter-Strike 2, Team Fortress 2, Dota 2, and Steam collectibles.
- **Secure Configuration**: Stores sensitive information (e.g., Steam credentials, trade URLs) in a `.env` file, preferably configured through the GUI for ease of use.
- **Windows Compatibility**: Optimized for Windows environments, with simple setup via batch files.

## How It Works

1. **Ban Monitoring**:

   - The Python script (`BanChecker.py`) periodically scrapes the specified Steam profile for ban indicators using `requests` and `BeautifulSoup`.
   - It checks for phrases like "VAC Ban on record" or "Game Ban on record" in the profile's HTML.

2. **Ban Detection**:

   - Upon detecting a ban, the script triggers `SendTrade.js`, a Node.js script that logs into the monitored Steam account and creates a trade offer containing all tradable items.

3. **Trade Execution**:

   - The trade offer is sent to the backup account specified in the `.env` file.
   - If the `AutoAccept` option is enabled, `AutoAccept.js` runs on the backup account to automatically accept the trade.

4. **GUI Interface**:

   - The PyQt5 GUI (`BanShieldGUI.py`) is the primary way to launch and interact with BanShield-V2. It provides an interface to configure settings, start/stop the bot, and view real-time logs and status updates.
   - Logs are color-coded for easy identification of actions, errors, and ban detection events.
   - The `.env` file is preferably edited through the GUI for convenience, though manual editing is also possible.

5. **Security**:

   - Trade offers include a unique, randomly generated key to ensure the correct trade is accepted by the backup account.

## Prerequisites

To run BanShield-V2, you need the following:

- **Windows Operating System**: The tool is designed and tested for Windows environments.
- **Python 3.8+**: For running the ban monitoring and GUI scripts.
- **Node.js 14+**: For executing the trade-related scripts.
- **Steam Account Credentials**: For both the monitored account and the backup account, including:
  - Username
  - Password
  - Shared Secret (for 2FA)
  - Identity Secret (for trade confirmations)
  - Trade URL (for the backup account)
- **Steam Mobile/Desktop Authenticator**: Enabled on both accounts for two-factor authentication (2FA).
- **Internet Connection**: Required for Steam API interactions and profile scraping.

## Installation

1. **Clone the Repository**:

   ```bash
   git clone https://github.com/AkkayaKaan/BanShield-V2
   cd BanShield-V2
   ```

2. **Install Dependencies**:

   - Run the provided `install.bat` to install all required dependencies:

     ```bash
     install.bat
     ```
   - This installs Python dependencies (`PyQt5`, `requests`, `beautifulsoup4`, `python-dotenv`) and Node.js dependencies (`steam-user`, `steamcommunity`, `steam-tradeoffer-manager`, `steam-totp`, `dotenv`).

3. **Configure the** `.env` **File**:

   - Open the GUI by running `Start.bat` and use the settings panel to configure the `.env` file (recommended).
   - Alternatively, manually edit the `.env` file with the following template:

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
     ```
   - Ensure the `ProfileToWatch` is the public Steam profile URL of the account to monitor.
   - Obtain the `SharedSecret` and `IdentitySecret` from your Steam Mobile Authenticator (e.g., using tools like Steam Desktop Authenticator).
   - Set `AutoAccept=true` if you want the backup account to automatically accept trades.

4. **Run the Application**:

   - Launch the GUI using the provided `Start.bat`:

     ```bash
     Start.bat
     ```

## Usage

1. **Launch the GUI**:

   - Run `Start.bat` to open the BanShield-V2 graphical interface.

2. **Configure Settings**:

   - Click the ☰ button to open the settings panel.
   - Enter or verify the configuration details (Steam profile URL, credentials, etc.) in the GUI.
   - Click "Save Config" to update the `.env` file. (Manual editing of the `.env` file is possible but not recommended.)
   - The GUI ensures all required fields are filled correctly before saving.

3. **Start the Bot**:

   - Click "Start Bot" to begin monitoring the specified Steam profile.
   - The GUI will display real-time logs and status updates (e.g., "No Ban", "Ban Detected!", "Error").
   - The "Last Check" field shows the timestamp of the latest profile check.

4. **Stop the Bot**:

   - Click "Stop Bot" to halt monitoring and terminate the process.

5. **Ban Detection and Trade**:

   - If a ban is detected, the bot will:
     - Log the event in the GUI with an alert.
     - Trigger `SendTrade.js` to send all tradable items to the backup account.
     - Optionally run `AutoAccept.js` if `AutoAccept` is enabled.
   - A notification will appear, and the system may emit a beep (depending on your Windows settings).

## File Structure

- `BanShieldGUI.py`: The main PyQt5 GUI script for launching, configuring, and monitoring the application.
- `BanChecker.py`: The Python script that monitors the Steam profile for bans.
- `SendTrade.js`: The Node.js script that handles trade offer creation and item transfer.
- `AutoAccept.js`: The Node.js script for automatically accepting trades on the backup account.
- `.env`: Configuration file for storing sensitive information, preferably edited via the GUI.
- `install.bat`: Batch file for installing dependencies (Windows).
- `Start.bat`: Batch file for launching the GUI (Windows).

## Troubleshooting

- **Error: "ProfileToWatch is required!"**
  - Ensure the `ProfileToWatch` field in the GUI or `.env` file is set to a valid Steam profile URL.
- **Error: "TradeOfferManager session error"**
  - Verify that the Steam credentials and 2FA secrets are correct in the GUI or `.env` file.
  - Ensure the Steam Mobile Authenticator is active and synchronized.
- **Trade Fails**
  - Confirm that the backup account's trade URL is valid and that both accounts have 2FA enabled.
  - Check for Steam Guard restrictions (e.g., new device login delays).
- **GUI Not Responding**
  - Ensure all dependencies are installed by running `install.bat`.
  - Verify that Python 3.8+ and Node.js 14+ are installed.

## Security Considerations

- **Sensitive Information**: Never share your `.env` file or include it in version control. It contains sensitive Steam credentials and 2FA secrets. Use the GUI to edit it securely.
- **Steam Guard**: Ensure both accounts have Steam Mobile Authenticator enabled to avoid trade restrictions.
- **Backup Account**: Use a trusted backup account to receive items, as it will have full access to the transferred inventory.
- **Network Security**: Run BanShield-V2 on a secure network to prevent interception of Steam API requests.

## Contributing

Contributions are welcome! Please follow these steps:

1. Fork the repository.
2. Create a new branch (`git checkout -b feature/your-feature`).
3. Make your changes and commit (`git commit -m "Add your feature"`).
4. Push to the branch (`git push origin feature/your-feature`).
5. Open a pull request with a detailed description of your changes.

## License

This project is licensed under the MIT License. See the LICENSE file for details.

## Acknowledgments

- Created by **Kaan Akkaya**.
- Built using PyQt5, BeautifulSoup, steam-user, and other open-source libraries.

## Disclaimer

This tool is provided for educational and personal use only. The author is not responsible for any misuse, account bans, or loss of items resulting from the use of this software. Use at your own risk, and ensure compliance with Steam's Terms of Service.