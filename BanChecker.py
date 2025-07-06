import subprocess
import requests
from bs4 import BeautifulSoup
import time
import os
from dotenv import load_dotenv

# Load the .env file ALWAYS with the latest version
load_dotenv(override=True)

# Fetch all settings (these are from .env)
STEAM_PROFILE = os.getenv("ProfileToWatch", "")
WATCHING_PROFILE_USERNAME = os.getenv("WatchingProfileUsername", "")
WATCHING_PROFILE_PASSWORD = os.getenv("WatchingProfilePassword", "")
WATCHING_PROFILE_SHARED_SECRET = os.getenv("WatchingProfileSharedSecret", "")
WATCHING_PROFILE_IDENTITY_SECRET = os.getenv("WatchingProfileIdentitySecret", "")
BANK_ACCOUNT_TRADE_URL = os.getenv("BankAccountTradeURL", "")
BANK_ACCOUNT_USERNAME = os.getenv("BankAccountUsername", "")
BANK_ACCOUNT_PASSWORD = os.getenv("BankAccountPassword", "")
BANK_ACCOUNT_SHARED_SECRET = os.getenv("BankAccountSharedSecret", "")
AUTO_ACCEPT = os.getenv("AutoAccept", "false")

CHECK_INTERVAL = 60  # seconds

BAN_PATTERNS = [
    "vac ban on record",
    "game ban on record"
]

def prepare_profile_url(url):
    if "?l=english" in url:
        return url
    if "?" in url:
        return url + "&l=english"
    return url + "?l=english"

def check_ban(profile_url):
    try:
        resp = requests.get(profile_url, timeout=10)
        if resp.status_code != 200:
            return f"[ERROR] HTTP {resp.status_code}"
        soup = BeautifulSoup(resp.text, "html.parser")

        ban_text = soup.find(
            string=lambda t: t and any(pattern in t.lower() for pattern in BAN_PATTERNS)
        )
        if ban_text:
            return f"[ALERT] BAN DETECTED: {ban_text.strip()}"
        return "[OK] NO BAN"
    except Exception as e:
        return f"[ERROR] {str(e)}"

if __name__ == "__main__":
    print("[INFO] BanChecker.py started.", flush=True)
    if not STEAM_PROFILE:
        print("[ERROR] ProfileToWatch not found! Check the .env file and ProfileToWatch value.", flush=True)
        exit(1)

    profile_url = prepare_profile_url(STEAM_PROFILE)
    while True:
        print(f"[CHECK] {time.strftime('%Y-%m-%d %H:%M:%S')} | Checking profile: {profile_url}", flush=True)
        result = check_ban(profile_url)
        print(f"{time.strftime('%Y-%m-%d %H:%M:%S')} {result}", flush=True)

        if "[ALERT]" in result:
            print("[ACTION] Ban detected, SendTrade.js starting...", flush=True)
            try:
                result = subprocess.run(["node", "SendTrade.js"], capture_output=True, text=True)
                if result.returncode != 0:
                    print(f"[ERROR] SendTrade.js failed to run: {result.stderr}", flush=True)
                else:
                    print(f"[INFO] SendTrade.js ran: {result.stdout}", flush=True)
            except Exception as e:
                print(f"[ERROR] Error while starting SendTrade.js: {str(e)}", flush=True)
            print("[INFO] SendTrade.js finished, BanChecker.py shutting down.", flush=True)
            exit(0)

        time.sleep(CHECK_INTERVAL)