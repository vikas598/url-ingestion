from pathlib import Path
import json
import time

SESSION_TIMEOUT_SECONDS = 15 * 60 
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
                "product_type": None,
                "preferences": [],
                "intent": None,
                "last_products": [],
                "last_query": None,
                "history": [],
                "last_updated": now
            }

    # SESSION TIMEOUT CHECK
    if now - memory.get("last_updated", 0) > SESSION_TIMEOUT_SECONDS:
        memory = {
            "budget": None,
            "category": None,
            "product_type": None,
            "preferences": [],
            "intent": None,
            "last_products": [],
            "last_query": None,
            "history": [],
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

        # Special handling for different keys
        if key == "last_products":
            # Always REPLACE last_products with new search results
            memory[key] = value
        elif isinstance(memory.get(key), list) and key == "preferences":
            # Only append to preferences list
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


def append_message(session_id: str, role: str, content: str):
    """
    Append a message to the conversation history.
    """
    memory = load_memory(session_id)
    
    if "history" not in memory:
        memory["history"] = []
    
    # Simple timestamp for sorting if needed later, though list order is enough
    timestamp = time.time()
    
    # Create message object
    new_message = {
        "role": role,
        "content": content,
        "timestamp": timestamp
    }
    
    # Append and check limit
    memory["history"].append(new_message)
    
    # Keep only last 20 messages
    if len(memory["history"]) > 20:
        memory["history"] = memory["history"][-20:]
        
    # We use update_memory but explicitly set history to avoid recursion or complex merge logic
    # Actually update_memory merges keys, so we can just pass the new history list
    update_memory(session_id, {"history": memory["history"]})
