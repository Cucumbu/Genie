import os

from dotenv import load_dotenv

load_dotenv()

MEETING_LINK = os.getenv("MEETING_LINK", "")
BOT_NAME = os.getenv("BOT_NAME", "Genie")
WAKE_WORD = os.getenv("WAKE_WORD", "genie")

# Optional: point to chrome.exe if auto-detection does not work.
CHROME_PATH = os.getenv("CHROME_PATH", "")
# Dedicated profile directory for a bot account login session.
BOT_PROFILE_DIR = os.getenv("BOT_PROFILE_DIR", ".bot_chrome_profile")

MODEL_SIZE = os.getenv("MODEL_SIZE", "tiny")

HACK_AI_API_KEY = os.getenv("HACK_AI_API_KEY", "")
API_KEY = HACK_AI_API_KEY
BASE_URL = "https://ai.hackclub.com/models"
MODEL_NAME = "google/gemini-3-flash-preview"