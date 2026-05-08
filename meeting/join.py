import shutil
import subprocess
from pathlib import Path

from playwright.sync_api import TimeoutError as PlaywrightTimeoutError
from playwright.sync_api import sync_playwright

from config import BOT_NAME, BOT_PROFILE_DIR, CHROME_PATH, JOIN_MODE, MEETING_LINK

_guest_playwright = None
_guest_browser = None
_guest_context = None


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


def _click_first(page, selectors, timeout=5000):
    for selector in selectors:
        try:
            page.locator(selector).first.click(timeout=timeout)
            return True
        except Exception:
            continue

    return False


def _fill_first(page, selectors, value, timeout=5000):
    for selector in selectors:
        try:
            locator = page.locator(selector).first
            locator.wait_for(state="visible", timeout=timeout)
            locator.fill(value)
            return True
        except Exception:
            continue

    return False


def _prepare_meet_ui(page):
    _click_first(
        page,
        [
            "button:has-text('Got it')",
            "button:has-text('I agree')",
            "button:has-text('Accept all')",
            "button:has-text('No thanks')",
        ],
        timeout=2500,
    )

    # Best effort: join with camera and mic disabled.
    for label in ["Turn off microphone", "Turn off mic", "Turn off camera"]:
        try:
            button = page.get_by_label(label)
            if button.count() > 0:
                button.first.click(timeout=1500)
        except Exception:
            continue


def _confirm_joined(prompt):
    answer = input(prompt).strip().lower()
    return answer in {"", "y", "yes"}


def _wait_for_join_confirmation(page, timeout_ms=30000):
    joined_selectors = [
        "button[aria-label*='Leave call']",
        "button[aria-label*='Leave the call']",
        "button:has-text('Leave call')",
        "button:has-text('Leave')",
        "div:has-text('You are the only one here')",
        "div:has-text('Meeting details')",
    ]

    try:
        page.wait_for_url("**/meeting/**", timeout=timeout_ms)
        return True
    except PlaywrightTimeoutError:
        pass

    for selector in joined_selectors:
        try:
            page.locator(selector).first.wait_for(state="visible", timeout=2500)
            return True
        except Exception:
            continue

    return False


def cleanup_guest_session():
    global _guest_browser, _guest_context, _guest_playwright

    if _guest_context is not None:
        try:
            _guest_context.close()
        except Exception:
            pass
        _guest_context = None

    if _guest_browser is not None:
        try:
            _guest_browser.close()
        except Exception:
            pass
        _guest_browser = None

    if _guest_playwright is not None:
        try:
            _guest_playwright.stop()
        except Exception:
            pass
        _guest_playwright = None


def _join_as_guest():
    global _guest_browser, _guest_context, _guest_playwright

    print("Opening Google Meet as a guest...")

    chrome_path = _resolve_chrome_path()
    launch_kwargs = {
        "headless": False,
        "args": ["--disable-blink-features=AutomationControlled"],
    }

    if chrome_path:
        launch_kwargs["executable_path"] = chrome_path
    else:
        print("Chrome not found automatically. Falling back to Playwright Chromium.")

    try:
        cleanup_guest_session()
        _guest_playwright = sync_playwright().start()
        user_data_dir = str(Path(BOT_PROFILE_DIR).resolve() / "guest_session")
        launch_kwargs["user_data_dir"] = user_data_dir

        _guest_context = _guest_playwright.chromium.launch_persistent_context(**launch_kwargs)
        _guest_context.grant_permissions(["microphone", "camera"], origin="https://meet.google.com")
        _guest_browser = _guest_context.browser
        page = _guest_context.pages[0] if _guest_context.pages else _guest_context.new_page()
        page.goto(MEETING_LINK, wait_until="domcontentloaded", timeout=60000)
        _prepare_meet_ui(page)

        name_filled = _fill_first(
            page,
            [
                "input[aria-label='Your name']",
                "input[placeholder='Your name']",
                "input[type='text']",
            ],
            BOT_NAME,
            timeout=10000,
        )

        if not name_filled:
            print("Could not find the guest name field.")
            cleanup_guest_session()
            return False

        joined = _click_first(
            page,
            [
                "button:has-text('Ask to join')",
                "button:has-text('Join now')",
            ],
            timeout=10000,
        )

        if not joined:
            print("Could not find the Ask to join button automatically.")
            print("If the page is open, you can still click Ask to join manually.")

        print("Finish any browser prompts, then click Ask to join if needed.")
        print("Waiting for the host to admit Genie...")

        if _wait_for_join_confirmation(page):
            print("Meeting join confirmed.")
            return True

        print("Automatic join detection did not fire.")
        if _confirm_joined("When Genie is inside the meeting, press Enter to continue, or type 'n' to cancel: "):
            print("Proceeding with manual join confirmation.")
            return True

        print("Timed out waiting for the host to admit the guest account.")
        cleanup_guest_session()
        return False
    except Exception as exc:
        cleanup_guest_session()
        print(f"Guest join flow failed: {exc}")
        return False


def _join_with_profile():
    chrome_path = _resolve_chrome_path()
    if not chrome_path:
        print("Chrome not found automatically. Install Chrome or set CHROME_PATH in .env.")
        return False

    print("Opening Google Meet in Chrome with bot profile...")
    try:
        subprocess.Popen(
            [chrome_path, f"--user-data-dir={BOT_PROFILE_DIR}", MEETING_LINK],
            shell=False,
        )
    except Exception as exc:
        print(f"Could not launch Chrome profile mode: {exc}")
        return False

    answer = input("Join/admit in that Chrome window, then type 'y' and press Enter to continue: ").strip().lower()
    if answer != "y":
        print("Meeting join not confirmed.")
        return False

    print("Meeting join confirmed.")
    return True

def join_meeting():
    if not MEETING_LINK:
        print("MEETING_LINK is empty. Set it in .env or config.py.")
        return False

    if JOIN_MODE == "guest":
        return _join_as_guest()

    if JOIN_MODE == "profile":
        return _join_with_profile()

    print(f"Unsupported JOIN_MODE '{JOIN_MODE}'. Use 'guest' or 'profile'.")
    return False
