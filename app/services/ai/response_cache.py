from pathlib import Path
import json
import hashlib
import time

BASE_DIR = Path(__file__).resolve().parent
CACHE_DIR = BASE_DIR / "response_cache"
CACHE_DIR.mkdir(exist_ok=True)

CACHE_TTL_SECONDS = 30 * 60  # same as session timeout


def _hash_query(session_id: str, query: str) -> str:
    key = f"{session_id}:{query.strip().lower()}"
    return hashlib.sha256(key.encode()).hexdigest()


def get_cached_response(session_id: str, query: str):
    key = _hash_query(session_id, query)
    path = CACHE_DIR / f"{key}.json"

    if not path.exists():
        return None

    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    if time.time() - data["timestamp"] > CACHE_TTL_SECONDS:
        path.unlink(missing_ok=True)
        return None

    return data["response"]


def save_cached_response(session_id: str, query: str, response: str):
    key = _hash_query(session_id, query)
    path = CACHE_DIR / f"{key}.json"

    payload = {
        "query": query,
        "response": response,
        "timestamp": time.time()
    }

    with open(path, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)
