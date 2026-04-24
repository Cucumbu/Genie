from config import WAKE_WORD

def is_called(text):
    return WAKE_WORD in text

def extract_query(text):
    return text.replace(WAKE_WORD, "").strip()