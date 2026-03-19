from playwright.sync_api import sync_playwright
from config import MEETING_LINK, BOT_NAME

def join_meeting():
    p = sync_playwright().start()

    browser = p.chromium.launch(
        headless=False,
        args=['--use-fake-ui-for-media-stream', '--use-fake-device-for-media-stream'])
    context = browser.new_context()
    page = context.new_page()
    page.goto(MEETING_LINK)
    input("Login manually and press Enter to continue...")

    try:
        page.fill('input[type="text"]', BOT_NAME)
    except:
        pass

    try:
        page.click('text=Join now', timeout=10000)
    except:
        try:
            page.click('text=Ask to join', timeout=10000)
        except:
            print("Could not find 'Join now' or 'Ask to join' button. Please join the meeting manually.")
    
    print("Joined the meeting successfully!")
    return browser,page