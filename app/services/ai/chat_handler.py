from app.services.ai.query_understanding import extract_query_intent
from app.services.recommender_system.search_service import search_products
from app.services.ai.reasoning_engine import generate_recommendation
from app.services.ai.conversation_store import load_memory, update_memory
from app.services.ai.response_cache import (
    get_cached_response,
    save_cached_response
)


def handle_user_message(session_id: str, user_input: str) -> str:
    """
    Central orchestration point for the AI assistant.
    """

    # 1️⃣ RESPONSE CACHE
    cached_response = get_cached_response(session_id, user_input)
    if cached_response:
        return cached_response

    # 2️⃣ LOAD MEMORY
    memory = load_memory(session_id)

    # 3️⃣ QUERY UNDERSTANDING
    parsed = extract_query_intent(user_input)

    # 4️⃣ EXPLICIT CATEGORY OVERRIDE (LLM)
    explicit_category = parsed.get("explicit_category")
    if explicit_category:
        update_memory(session_id, {"category": explicit_category})

    # 5️⃣ UPDATE MEMORY WITH CONSTRAINTS
    update_memory(session_id, {
        "budget": parsed["constraints"].get("budget"),
        "preferences": parsed["constraints"].get("preferences", []),
        "intent": parsed.get("intent")
    })

    # Reload memory after updates
    memory = load_memory(session_id)

    # 6️⃣ SEARCH (PASS MEMORY)
    products = search_products(
        query=parsed["rewritten_query"],
        k=5,
        memory=memory
    )

    update_memory(session_id, {
        "last_products": [p["title"] for p in products]
    })

    # 7️⃣ LLM REASONING
    reply = generate_recommendation(
        user_message=user_input,
        intent_data=parsed,
        products=products
    )

    # 8️⃣ SAVE RESPONSE CACHE
    save_cached_response(session_id, user_input, reply)

    return reply
