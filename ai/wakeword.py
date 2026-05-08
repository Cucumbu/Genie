import re

from config import WAKE_WORD

WAKE_WORD_PATTERN = re.compile(rf"\b{re.escape(WAKE_WORD)}\b", re.IGNORECASE)

def is_called(text):
    return bool(WAKE_WORD_PATTERN.search(text))

def extract_query(text):
    return WAKE_WORD_PATTERN.sub("", text, count=1).strip(" ,:.!?-")
