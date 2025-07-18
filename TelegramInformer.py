import os
import requests
from dotenv import load_dotenv

load_dotenv(override=True)

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "")

LAST_MESSAGE_FILE = ".telegram_last_message_id"

def send_log(log):
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print("[TELEGRAM] Bot token or chat id missing.")
        return

    # Delete the last message first
    last_message_id = None
    if os.path.exists(LAST_MESSAGE_FILE):
        with open(LAST_MESSAGE_FILE, "r") as f:
            last_message_id = f.read().strip()
    if last_message_id:
        try:
            delete_url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/deleteMessage"
            requests.post(delete_url, data={
                "chat_id": TELEGRAM_CHAT_ID,
                "message_id": last_message_id
            }, timeout=5)
        except Exception as e:
            print(f"[TELEGRAM] Could not delete previous message: {e}")

    # Send new message
    try:
        send_url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        resp = requests.post(send_url, data={
            "chat_id": TELEGRAM_CHAT_ID,
            "text": str(log)
        }, timeout=5)
        if resp.ok:
            message_id = resp.json()["result"]["message_id"]
            with open(LAST_MESSAGE_FILE, "w") as f:
                f.write(str(message_id))
            print(f"[TELEGRAM] Log sent: {log}")
        else:
            print(f"[TELEGRAM] Failed to send message: {resp.text}")
    except Exception as e:
        print(f"[TELEGRAM] Failed to send message: {e}")

def reset_channel():
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print("[TELEGRAM] Bot token or chat id missing (reset).")
        return

    # Send a dummy message to get the latest message_id
    try:
        send_url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        resp = requests.post(send_url, data={
            "chat_id": TELEGRAM_CHAT_ID,
            "text": "reset_dummy"
        }, timeout=5)
        if resp.ok:
            base_id = resp.json()["result"]["message_id"]
        else:
            print(f"[TELEGRAM] Failed to send dummy message for reset: {resp.text}")
            return
    except Exception as e:
        print(f"[TELEGRAM] Failed to send dummy message for reset: {e}")
        return

    # Try deleting the last 15 messages (from base_id-14 to base_id)
    deleted = 0
    for mid in range(base_id-14, base_id+1):
        try:
            del_url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/deleteMessage"
            resp = requests.post(del_url, data={"chat_id": TELEGRAM_CHAT_ID, "message_id": mid}, timeout=5)
            if resp.ok:
                print(f"[TELEGRAM] Channel reset: Deleted message {mid}")
                deleted += 1
        except Exception as e:
            continue

    # Remove local last_message_id file
    if os.path.exists(LAST_MESSAGE_FILE):
        os.remove(LAST_MESSAGE_FILE)
    print(f"[TELEGRAM] Channel reset complete. {deleted} messages deleted.")
