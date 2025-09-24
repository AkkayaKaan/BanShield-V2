# BanChecker.py — Dry-Run (Simulation) entegre tam sürüm
import subprocess
import requests
from bs4 import BeautifulSoup
import time
import os
import sys
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

STEAM_PROFILE   = os.getenv("ProfileToWatch", "")
TELEGRAM_NOTIFY = os.getenv("TelegramNotify", "true").lower() == "true"

CHECK_INTERVAL = int(os.getenv("CHECK_INTERVAL", "20"))
if CHECK_INTERVAL < 20: CHECK_INTERVAL = 20
if CHECK_INTERVAL > 300: CHECK_INTERVAL = 300

# --- Dry-Run (Simulation) bayrağı ---
IS_DRY_RUN = (os.getenv("BANSHIELD_DRY_RUN") == "1") or ("--dry-run" in sys.argv)

# Simülasyon parametreleri (ilk kontrolde asla tetiklemez)
import random
_sim_trigger_check = None     # 3..10
_sim_triggered     = False
_sim_ban_kind      = None     # "VAC" veya "Game"

def _init_sim_once():
    global _sim_trigger_check, _sim_ban_kind
    if _sim_trigger_check is None:
        _sim_trigger_check = random.randint(3, 10)
        _sim_ban_kind = random.choice(["VAC", "Game"])

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

# YENİ HALİ (Bunu kullanacaksın)
def check_ban(profile_url):
    """
    Steam profilini kontrol eder. Sadece "0 day(s) since last ban" metnini
    içeren YENİ ban durumlarında [ALERT] döndürür. Eski banları tolere eder.
    """
    try:
        resp = requests.get(profile_url, timeout=10)
        if resp.status_code != 200:
            return f"[ERROR] HTTP {resp.status_code}"
        
        soup = BeautifulSoup(resp.text, "html.parser")
        
        # Sayfada "day(s) since last ban" içeren bir metin ara
        days_since_ban_element = soup.find(
            string=lambda t: t and "day(s) since last ban" in t.lower()
        )
        
        if days_since_ban_element:
            ban_text = days_since_ban_element.strip().lower()
            
            # Sadece "0 day(s)" içeren yeni banları yakala
            if "0 day(s) since last ban" in ban_text:
                # Bu yeni bir ban. Alarmı tetikle!
                return f"[ALERT] BAN DETECTED: {days_since_ban_element.strip()}"
            else:
                # Bu eski bir ban. Logla ama programı normal akışında tut.
                return f"[OK] NO BAN (Old ban found: {days_since_ban_element.strip()})"
        
        # Sayfada hiç ban bilgisi bulunamadı.
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

def run_sendtrade(dry_run: bool):
    """
    SendTrade.js'yi çalıştırır.
    dry_run=True iken env'e BANSHIELD_DRY_RUN=1 koyar; böylece SendTrade
    sadece item listesini yazar ve trade göndermez.
    """
    env = os.environ.copy()
    if dry_run:
        env["BANSHIELD_DRY_RUN"] = "1"
    try:
        result_proc = subprocess.run(["node", "SendTrade.js"], capture_output=True, text=True, env=env)
        if result_proc.returncode != 0:
            print(f"[ERROR] SendTrade.js failed to run: {result_proc.stderr}", flush=True)
        else:
            print(f"[INFO] SendTrade.js ran: {result_proc.stdout}", flush=True)
        return result_proc.returncode
    except Exception as e:
        print(f"[ERROR] Error while starting SendTrade.js: {str(e)}", flush=True)
        return 1

if __name__ == "__main__":
    print("[INFO] BanChecker.py started.", flush=True)
    reset_channel()

    if not STEAM_PROFILE:
        print("[ERROR] ProfileToWatch not found! Check the .env file and the value of ProfileToWatch.", flush=True)
        exit(1)

    profile_url = prepare_profile_url(STEAM_PROFILE)
    check_count = 0

    if IS_DRY_RUN:
        _init_sim_once()
        print(f"[DRY-RUN] Simulation enabled. Will randomly trigger at check #{_sim_trigger_check} with kind={_sim_ban_kind}.", flush=True)
    else:
        print("[LIVE] Dry-run disabled. Normal ban monitoring is active.", flush=True)

    while True:
        check_count += 1
        print(f"[CHECK] {time.strftime('%Y-%m-%d %H:%M:%S')} | Checking profile: {profile_url}", flush=True)

        result = check_ban(profile_url)

        # Hata durumunda canlı/dry-run fark etmeksizin aynı davranış
        if "[ERROR]" in result:
            print(f"{time.strftime('%Y-%m-%d %H:%M:%S')} {result}", flush=True)
            if TELEGRAM_NOTIFY:
                send_log(result)
            time.sleep(CHECK_INTERVAL)
            continue

        # --- DRY-RUN: 3–10. kontrol arasında rastgele simüle edilmiş ban ---
        if IS_DRY_RUN and (not _sim_triggered) and check_count >= 2 and (check_count == _sim_trigger_check):
            _sim_triggered = True
            sim_msg = f"[DRY-RUN] {_sim_ban_kind} ban detected (simulated) at check #{check_count}."
            print(sim_msg, flush=True)
            if TELEGRAM_NOTIFY:
                # Simülasyon olduğunu belli eden kısa log
                send_log(sim_msg)

            # Simülasyonda multi-check ile oyalama yok; doğrudan SendTrade'i DRY-RUN olarak çalıştır.
            rc = run_sendtrade(dry_run=True)

            # Simülasyonda WatchDog başlatmayız.
            print("[DRY-RUN] Simulation flow finished. BanChecker.py shutting down.", flush=True)
            exit(0)

        # --- LIVE: gerçek akış ---
        if "[ALERT]" in result:
            ban_confirmed, details = multi_check_ban(profile_url, total_checks=10, wait_seconds=5, min_alerts=2)
            if ban_confirmed:
                if TELEGRAM_NOTIFY:
                    send_log(1)
                print(f"{time.strftime('%Y-%m-%d %H:%M:%S')} [ACTION] Ban detected in multiple checks, starting SendTrade.js...", flush=True)

                rc = run_sendtrade(dry_run=False)

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
