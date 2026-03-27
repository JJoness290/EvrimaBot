import json
import time
from pathlib import Path
from datetime import datetime

ANNOUNCEMENT_QUEUE_FILE = Path("announcement_queue.json")
WINDOW_TITLE_CONTAINS = "Evrima RCON"
REQUIRE_EXISTING_WINDOW = True


def load_json(path: Path, default):
    if path.exists():
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            return default
    return default


def save_json(path: Path, data):
    path.write_text(json.dumps(data, indent=2), encoding="utf-8")


def load_queue():
    return load_json(ANNOUNCEMENT_QUEUE_FILE, [])


def save_queue(data):
    save_json(ANNOUNCEMENT_QUEUE_FILE, data)


def find_pending_job(queue_data):
    for job in queue_data:
        if job.get("status") == "PENDING":
            return job
    return None


def find_existing_rcon_window():
    try:
        import pygetwindow as gw
    except Exception:
        print("[RCON GUI EXECUTOR] FAILED (pyautogui/pygetwindow not available)")
        return None

    try:
        matching = []
        for title in gw.getAllTitles():
            if title and WINDOW_TITLE_CONTAINS.lower() in title.lower():
                matching.append(title)

        if not matching:
            return None

        target_window = gw.getWindowsWithTitle(matching[0])[0]
        return target_window
    except Exception:
        return None


def execute_announcement_with_gui(message: str) -> bool:
    try:
        import pyautogui
    except Exception:
        print("[RCON GUI EXECUTOR] FAILED (pyautogui/pygetwindow not available)")
        return False

    try:
        target_window = None
        if REQUIRE_EXISTING_WINDOW:
            target_window = find_existing_rcon_window()
            if not target_window:
                print("[RCON GUI EXECUTOR] Window not found, announcement left pending")
                return False
            print("[RCON GUI EXECUTOR] Found existing window")

        target_window.activate()
        time.sleep(0.6)

        pyautogui.click()
        time.sleep(0.2)
        pyautogui.hotkey("ctrl", "a")
        time.sleep(0.1)
        pyautogui.press("backspace")
        time.sleep(0.1)

        command = f"announce {message}"
        pyautogui.typewrite(command, interval=0.02)
        time.sleep(0.2)
        pyautogui.press("enter")
        time.sleep(0.6)

        return True
    except Exception:
        return False


def process_queue_once():
    queue_data = load_queue()
    job = find_pending_job(queue_data)
    if not job:
        return

    message = str(job.get("message", "")).strip()
    if not message:
        job["status"] = "FAILED"
        job["completed_at"] = str(datetime.now())
        save_queue(queue_data)
        print("[RCON GUI EXECUTOR] FAILED")
        return

    print(f"[RCON GUI EXECUTOR] Executing announcement: {message}")
    success = execute_announcement_with_gui(message)

    if success:
        job["status"] = "DONE"
        job["completed_at"] = str(datetime.now())
        save_queue(queue_data)
        print("[RCON GUI EXECUTOR] DONE")
    else:
        existing_window = find_existing_rcon_window()
        if REQUIRE_EXISTING_WINDOW and not existing_window:
            print("[RCON GUI EXECUTOR] Window not found, leaving pending")
            return
        job["status"] = "FAILED"
        job["completed_at"] = str(datetime.now())
        save_queue(queue_data)
        print("[RCON GUI EXECUTOR] FAILED")


def main():
    print("[RCON GUI EXECUTOR] started")
    while True:
        try:
            process_queue_once()
        except Exception as e:
            print(f"[RCON GUI EXECUTOR] FAILED {e}")
        time.sleep(1.0)


if __name__ == "__main__":
    main()
