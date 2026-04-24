import shutil
import subprocess

from config import BOT_PROFILE_DIR, CHROME_PATH, MEETING_LINK


def _resolve_chrome_path():
    if CHROME_PATH:
        return CHROME_PATH

    candidates = [
        shutil.which("chrome"),
        shutil.which("chrome.exe"),
        r"C:\Program Files\Google\Chrome\Application\chrome.exe",
        r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
    ]

    for candidate in candidates:
        if candidate:
            return candidate

    return None

def join_meeting():
    if not MEETING_LINK:
        print("MEETING_LINK is empty. Set it in .env or config.py.")
        return False

    chrome_path = _resolve_chrome_path()
    if chrome_path:
        print("Opening Google Meet in Chrome with bot profile...")
        try:
            subprocess.Popen(
                [chrome_path, f"--user-data-dir={BOT_PROFILE_DIR}", MEETING_LINK],
                shell=False,
            )
        except Exception as exc:
            print(f"Could not launch Chrome profile mode: {exc}")
            return False
    else:
        print("Chrome not found automatically. Install Chrome or set CHROME_PATH in .env.")
        return False

    answer = input("Join/admit in that Chrome window, then type 'y' and press Enter to continue: ").strip().lower()
    if answer != "y":
        print("Meeting join not confirmed.")
        return False

    print("Meeting join confirmed.")
    return True