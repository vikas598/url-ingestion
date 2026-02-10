from pathlib import Path
import json
import time

SESSION_TIMEOUT_SECONDS = 30 * 60 
BASE_DIR = Path(__file__).resolve().parent
MEMORY_DIR = BASE_DIR / "conversation_memory"
MEMORY_DIR.mkdir(exist_ok=True)

# In-memory cache
_sessions = {}


def _get_session_path(session_id: str) -> Path:
    return MEMORY_DIR / f"{session_id}.json"


def load_memory(session_id: str) -> dict:
    now = time.time()

    if session_id in _sessions:
        memory = _sessions[session_id]
    else:
        path = _get_session_path(session_id)
        if path.exists():
            with open(path, "r", encoding="utf-8") as f:
                memory = json.load(f)
        else:
            memory = {
                "budget": None,
                "category": None,
                "preferences": [],
                "intent": None,
                "last_products": [],
                "last_updated": now
            }

    # SESSION TIMEOUT CHECK
    if now - memory.get("last_updated", 0) > SESSION_TIMEOUT_SECONDS:
        memory = {
            "budget": None,
            "category": None,
            "preferences": [],
            "intent": None,
            "last_products": [],
            "last_updated": now
        }

    memory["last_updated"] = now
    _sessions[session_id] = memory
    return memory


def update_memory(session_id: str, updates: dict):
    """
    Update memory fields safely.
    """
    memory = load_memory(session_id)

    for key, value in updates.items():
        if value is None:
            continue

        if isinstance(memory.get(key), list):
            for item in value:
                if item not in memory[key]:
                    memory[key].append(item)
        else:
            memory[key] = value

    # Persist to disk
    path = _get_session_path(session_id)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(memory, f, indent=2)

    _sessions[session_id] = memory
