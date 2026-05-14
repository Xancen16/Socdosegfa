import re
from config import InitialDataConfig


def clean_user_text(raw_text):
    if not raw_text:
        return ""

    raw_text = raw_text.lower().strip()

    for word in InitialDataConfig.NOISE_WORDS:
        raw_text = raw_text.replace(word, "")

    cleaned = re.sub(r'\s+', ' ', raw_text).strip()

    return cleaned


def extract_budget(text):
    match = re.search(r'(\d+)\s*(?:руб|рублей|р)?', text)
    return match.group(1) if match else None


def normalize_store_name(store_name):
    return store_name.lower().strip()