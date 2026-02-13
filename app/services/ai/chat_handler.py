import re
from app.services.ai.query_understanding import extract_query_intent
from app.services.recommender_system.search_service import search_products
from app.services.ai.reasoning_engine import generate_recommendation, generate_catalog_summary
from app.services.ai.conversation_store import load_memory, update_memory, append_message
from app.services.ai.response_cache import (
    get_cached_response,
    save_cached_response
)
from app.services.ai.small_talk import generate_small_talk_response



def handle_user_message(session_id: str, user_input: str) -> tuple[str, list]:
    # 0️⃣ SAVE USER MESSAGE
    append_message(session_id, "user", user_input)

    # 1️⃣ MEMORY
    memory = load_memory(session_id)
    history = memory.get("history", [])

    # 2️⃣ INTENT
    parsed = extract_query_intent(user_input, history=history)
    intent = parsed.get("intent")
    print(f"DEBUG: Intent='{intent}', rewritten_query='{parsed.get('rewritten_query')}'", flush=True)
    print(f"DEBUG: Memory last_query='{memory.get('last_query')}'", flush=True)

    # 3️⃣ CACHE (Skip for follow-up questions that need memory products)
    is_followup = (intent in ["comparison", "info"]) and not parsed.get("rewritten_query")
    
    # Save last_query BEFORE cache check so combo_upsell always has it
    rewritten_query = parsed.get("rewritten_query")
    if rewritten_query:
        update_memory(session_id, {"last_query": rewritten_query})
        print(f"DEBUG: Saved last_query='{rewritten_query}' early (before cache)", flush=True)
    
    if not is_followup and intent != "combo_upsell":
        cached = get_cached_response(session_id, user_input)
        if cached:
            append_message(session_id, "assistant", cached)
            return cached, []

    # SMALL TALK
    if intent == "small_talk":
        reply = generate_small_talk_response(user_input)
        save_cached_response(session_id, user_input, reply)
        append_message(session_id, "assistant", reply)
        return reply, []

    # WEBSITE INFO
    if intent == "website_info":
        reply = generate_catalog_summary(user_input)
        save_cached_response(session_id, user_input, reply)
        append_message(session_id, "assistant", reply)
        return reply, []

    # COMBO UPSELL
    if intent == "combo_upsell":
        last_query = memory.get("last_query")
        if last_query:
            combo_products = search_products(
                query=last_query,
                k=3,
                memory=memory,
                product_type="combo"
            )
            if combo_products:
                update_memory(session_id, {"last_products": combo_products, "product_type": "combo"})
                reply, selected_ids = generate_recommendation(
                    user_message=user_input,
                    intent_data=parsed,
                    products=combo_products,
                    history=history
                )
                final_products = []
                if selected_ids:
                    selected_set = set(selected_ids)
                    final_products = [p for p in combo_products if p.get('product_id') in selected_set]
                save_cached_response(session_id, user_input, reply)
                append_message(session_id, "assistant", reply)
                return reply, final_products
            else:
                reply = "Sorry, I couldn't find any combo packs for that product. Is there anything else I can help with?"
                append_message(session_id, "assistant", reply)
                return reply, []
        else:
            reply = "I'm not sure what product you'd like combos for. Could you tell me what you're looking for?"
            append_message(session_id, "assistant", reply)
            return reply, []

    # FOLLOW-UP QUESTIONS (NO SEARCH)
    # Handle both comparison and info intents without new search
    if is_followup:
        products = memory.get("last_products", [])
        
        # If no products in memory, but we have history, maybe LLM can answer from general knowledge or history
        if not products and not history:
             reply = "I need to show you some options first before I can answer that."
             append_message(session_id, "assistant", reply)
             return reply, []

        reply, selected_ids = generate_recommendation(
            user_message=user_input,
            intent_data=parsed,
            products=products,
            history=history
        )
        
        final_products = []
        if selected_ids:
            selected_set = set(selected_ids)
            final_products = [p for p in products if p.get('product_id') in selected_set]

        save_cached_response(session_id, user_input, reply)
        append_message(session_id, "assistant", reply)
        return reply, final_products

    # 4️⃣ CATEGORY OVERRIDE
    if parsed.get("explicit_category"):
        update_memory(session_id, {"category": parsed["explicit_category"]})

    # 5️⃣ CONSTRAINTS (SAFE)
    constraints = parsed.get("constraints") or {}
    
    # Normalize Budget
    raw_budget = constraints.get("budget")
    normalized_budget = None
    if raw_budget:
        # Extract first number found in string
        match = re.search(r"\d+", str(raw_budget))
        if match:
            normalized_budget = int(match.group())

    update_memory(session_id, {
        "budget": normalized_budget,
        "preferences": constraints.get("preferences", []),
        "intent": intent
    })
    
    # Reload memory to get latest state if needed, though we just updated it
    memory = load_memory(session_id)

    # 6️⃣ SEARCH (ONLY HERE)
    rewritten_query = parsed.get("rewritten_query")
    if not rewritten_query:
        reply = "Could you please clarify what you’re looking for?"
        append_message(session_id, "assistant", reply)
        return reply, []

    # Get Filter
    product_type_filter = parsed.get("product_type_filter", "single") 
    print(f"DEBUG: Intent Filter: {product_type_filter}", flush=True) 


    products = search_products(
        query=rewritten_query,
        k=3,
        memory=memory,
        product_type=product_type_filter
    )

    # 🔹 FALLBACK LOGIC: If "single" search yields poor results, try "any" (Combos)
    if product_type_filter == "single" and rewritten_query and products:
        # Simple keyword matching to check relevance
        # (We reuse the query intent keywords or just simple split)
        keywords = [w.lower() for w in rewritten_query.split() if len(w) > 2]
        
        if keywords:
            valid_matches = 0
            for p in products:
                p_text = (p.get('title', '') + ' ' + str(p.get('category', ''))).lower()
                if any(kw in p_text for kw in keywords):
                    valid_matches += 1
            
            # Use strict threshold: If we found fewer than 2 relevant items, try expanding
            # For "idli", single search finds 1 item. Fallback => finds 5 items.
            if valid_matches < 2:
                print(f"DEBUG: Low relevance ({valid_matches} matches) for 'single'. Falling back to 'any'.", flush=True)
                expanded_products = search_products(
                    query=rewritten_query,
                    k=3,
                    memory=memory,
                    product_type="any"
                )
                
                # Check if expansion actually helped
                expanded_matches = 0
                for p in expanded_products:
                    p_text = (p.get('title', '') + ' ' + str(p.get('category', ''))).lower()
                    if any(kw in p_text for kw in keywords):
                        expanded_matches += 1
                
                if expanded_matches > valid_matches:
                    print(f"DEBUG: Fallback successful. Found {expanded_matches} matches.", flush=True)
                    products = expanded_products
                    product_type_filter = "any" # Update tracking


    update_memory(session_id, {
        "last_products": products,
        "last_query": rewritten_query,
        "product_type": product_type_filter
    })
    print(f"DEBUG: Saved last_query='{rewritten_query}' to memory", flush=True)

    # 7️⃣ REASONING
    reply, selected_ids = generate_recommendation(
        user_message=user_input,
        intent_data=parsed,
        products=products,
        history=history
    )

    # Filter products for frontend display based on reasoning selection
    final_products = []
    if selected_ids:
        print(f"DEBUG: Selected IDs: {selected_ids}", flush=True)
        selected_set = set(selected_ids)
        final_products = [p for p in products if p.get('product_id') in selected_set]
    
    # If LLM triggered fallback (no tag found), selected_ids would be all products, so final_products = products.
    # If LLM output empty tag, final_products = [].

    save_cached_response(session_id, user_input, reply)
    append_message(session_id, "assistant", reply)
    return reply, final_products
