from .category_config import NAV_CATEGORIES

STOP_WORDS = {
    "i", "want", "need", "show", "me", "find", "looking",
    "for", "a", "an", "the", "with", "and", "or"
}

def extract_keywords(text: str) -> list[str]:
    words = text.lower().split()
    return [w for w in words if w not in STOP_WORDS and len(w) > 2]


def detect_category(text: str) -> str | None:
    text = text.lower()
    for category, keywords in NAV_CATEGORIES.items():
        for kw in keywords:
            if kw in text:
                return category
    return None
