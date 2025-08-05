import subprocess
import requests
from bs4 import BeautifulSoup
import time
import os
from dotenv import load_dotenv
from TelegramInformer import send_log, reset_channel

PID_FILE = "banshield.pid"

def write_pid():
    with open(PID_FILE, "w") as f:
        f.write(str(os.getpid()))

def remove_pid():
    if os.path.exists(PID_FILE):
        os.remove(PID_FILE)

write_pid()
load_dotenv(override=True)

STEAM_PROFILE = os.getenv("ProfileToWatch", "")
TELEGRAM_NOTIFY = os.getenv("TelegramNotify", "true").lower() == "true"

CHECK_INTERVAL = int(os.getenv("CHECK_INTERVAL", "20"))
if CHECK_INTERVAL < 20: CHECK_INTERVAL = 20
if CHECK_INTERVAL > 300: CHECK_INTERVAL = 300

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

def launch_watchdog():
    try:
        subprocess.Popen('start "" node WatchDog.js', shell=True)
        print("[INFO] WatchDog.js launched in a new console window.", flush=True)
    except Exception as e:
        print(f"[ERROR] Failed to launch WatchDog.js: {str(e)}", flush=True)

def multi_check_ban(profile_url, total_checks=10, wait_seconds=5, min_alerts=2):
    alerts = 0
    errors = 0
    results = []
    for i in range(total_checks):
        result = check_ban(profile_url)
        results.append(result)
        print(f"[MULTI-CHECK {i+1}/{total_checks}] {time.strftime('%Y-%m-%d %H:%M:%S')} | {result}", flush=True)
        if "[ALERT]" in result:
            alerts += 1
        if "[ERROR]" in result:
            errors += 1
        time.sleep(wait_seconds)
    print(f"[SUMMARY] Ban detected in {alerts} out of {total_checks} checks. Errors: {errors}", flush=True)
    if alerts >= min_alerts:
        return True, results
    return False, results

if __name__ == "__main__":
    print("[INFO] BanChecker.py started.", flush=True)
    reset_channel()

    if not STEAM_PROFILE:
        print("[ERROR] ProfileToWatch not found! Check the .env file and the value of ProfileToWatch.", flush=True)
        exit(1)

    profile_url = prepare_profile_url(STEAM_PROFILE)
    while True:
        print(f"[CHECK] {time.strftime('%Y-%m-%d %H:%M:%S')} | Checking profile: {profile_url}", flush=True)
        result = check_ban(profile_url)

        if "[ERROR]" in result:
            print(f"{time.strftime('%Y-%m-%d %H:%M:%S')} {result}", flush=True)
            if TELEGRAM_NOTIFY:
                send_log(result)
            time.sleep(CHECK_INTERVAL)
            continue

        if "[ALERT]" in result:
            ban_confirmed, details = multi_check_ban(profile_url, total_checks=10, wait_seconds=5, min_alerts=2)
            if ban_confirmed:
                if TELEGRAM_NOTIFY:
                    send_log(1)
                print(f"{time.strftime('%Y-%m-%d %H:%M:%S')} [ACTION] Ban detected in multiple checks, starting SendTrade.js...", flush=True)
                try:
                    result_proc = subprocess.run(["node", "SendTrade.js"], capture_output=True, text=True)
                    if result_proc.returncode != 0:
                        print(f"[ERROR] SendTrade.js failed to run: {result_proc.stderr}", flush=True)
                    else:
                        print(f"[INFO] SendTrade.js ran: {result_proc.stdout}", flush=True)
                except Exception as e:
                    print(f"[ERROR] Error while starting SendTrade.js: {str(e)}", flush=True)
                try:
                    launch_watchdog()
                except Exception as e:
                    print(f"[ERROR] Error while starting WatchDog.js: {str(e)}", flush=True)
                print("[INFO] SendTrade.js finished, BanChecker.py shutting down.", flush=True)
                exit(0)
            else:
                print("[SAFEGUARD] Multiple checks indicate no reliable ban. False positive prevented.", flush=True)
                if TELEGRAM_NOTIFY:
                    send_log("[SAFEGUARD] False-positive ban alert prevented.")
        else:
            if TELEGRAM_NOTIFY:
                send_log(0)
            print(f"{time.strftime('%Y-%m-%d %H:%M:%S')} {result}", flush=True)

        time.sleep(CHECK_INTERVAL)

import atexit
atexit.register(remove_pid)
