import os

from dotenv import load_dotenv

load_dotenv()


def _env_bool(name: str, default: str = "false") -> bool:
    return os.getenv(name, default).strip().lower() in {"1", "true", "yes", "on"}

MEETING_LINK = os.getenv("MEETING_LINK", ""), os.getenv("MEETING_URL", "")
BOT_NAME = os.getenv("BOT_NAME", "Genie")
WAKE_WORD = os.getenv("WAKE_WORD", "genie")
JOIN_MODE = os.getenv("JOIN_MODE", "guest").strip().lower()
AUDIO_SOURCE = os.getenv("AUDIO_SOURCE", "loopback")

CHROME_PATH = os.getenv("CHROME_PATH", "")
BOT_PROFILE_DIR = os.getenv("BOT_PROFILE_DIR", ".bot_chrome_profile")

STT_PROVIDER = os.getenv("STT_PROVIDER", "azure").strip().lower()

AZURE_SPEECH_KEY = os.getenv("AZURE_SPEECH_KEY", "")
AZURE_SPEECH_REGION = os.getenv("AZURE_SPEECH_REGION", "eastus")
AZURE_SPEECH_LANGUAGE = os.getenv("AZURE_SPEECH_LANGUAGE", "")
AZURE_SPEECH_VOICE = os.getenv("AZURE_SPEECH_VOICE", "en-IN-NeerjaNeural")

TTS_ENABLED = _env_bool("TTS_ENABLED", "true")
TTS_PROVIDER = os.getenv("TTS_PROVIDER", "azure").strip().lower()


API_KEY = os.getenv("AZURE_OPENAI_KEY", "")
BASE_URL = os.getenv("AZURE_OPENAI_ENDPOINT", "")
MODEL_NAME = os.getenv("AZURE_OPENAI_DEPLOYMENT", "gpt-4o")
AZURE_API_VERSION = os.getenv("AZURE_API_VERSION", "2024-02-01")
