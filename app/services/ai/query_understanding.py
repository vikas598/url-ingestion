import json
import os
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

MODEL = "gpt-4o-mini"


def extract_query_intent(user_message: str, history: list = None) -> dict:
    """
    Uses LLM to classify user intent and (if applicable)
    rewrite shopping queries + extract constraints.
    """
    
    # Format History
    history_context = ""
    if history:
        history_context = "Recent Conversation History:\n"
        for msg in history[-5:]:  # Only show last 5 messages for context
            role = msg.get("role", "unknown")
            content = msg.get("content", "")
            history_context += f"- {role.upper()}: {content}\n"
        history_context += "\n"

    system_prompt = (
        "You are an AI assistant that classifies user messages and, when applicable, "
        "converts shopping queries into structured search data.\n\n"
        "Rules:\n"
        "- If the message is a greeting, casual conversation, or polite response "
        "(e.g. 'hi', 'how are you', 'thanks', 'ok'), classify intent as 'small_talk'.\n"
        "- For 'small_talk', set rewritten_query to null and constraints to null.\n"
        "- **COMBO UPSELL**: If the LAST assistant message asked about combo packs (e.g., 'Would you like to see combo packs?') "
        "and the user responds with 'yes', 'sure', 'show me', 'ok', or similar affirmative, classify intent as 'combo_upsell'. "
        "Set rewritten_query to null and product_type_filter to 'combo'.\n"
        "- **WEBSITE INFO**: If the user asks about the website, store, brand, catalog, or what products are available "
        "(e.g., 'tell me about your website', 'what do you sell?', 'what products do you have?', 'tell me about millex'), "
        "classify intent as 'website_info'. Set rewritten_query to null.\n"
        "- Do NOT invent products.\n"
        "- Do NOT answer the user.\n"
        "- Only return valid JSON.\n"
        "- Keep rewritten_query short and optimized for semantic search."
        "- Use the CONVERSATION HISTORY to understand context (e.g., 'show me more' refers to previous search)."
        "- DEFAULT product_type_filter to 'single' unless user asks for 'combo', 'pack', 'set', 'gift'."
    )

    user_prompt = f"""
{history_context}
User message:
"{user_message}"

Return JSON with:
- intent (one of: small_talk, recommendation, comparison, info, buy, combo_upsell, website_info)
- rewritten_query (string or null)
  * Set to NULL for follow-up questions like "tell me about product 1", "how do I cook it?"
  * Only set a value when user wants to search for NEW products
  * If user says "show me more" or "any others", rewrite query based on previous context.
- product_type_filter (string: "single", "combo", or "any")
  * "single": Default for general queries like "idli mix", "millet flakes".
  * "combo": If user mentions "combo", "pack", "kit", "set", "gift".
  * "any": If user explicitly says "all", "both", or context is mixed.
- constraints (object or null):
    - budget (string or null)
    - category (string or null)
    - preferences (array of strings)
- explicit_category (one of: special-offer, health-mix, ready-to-cook, combos, infant-food, or null)
"""

    response = client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        temperature=0
    )

    content = response.choices[0].message.content.strip()

    try:
        return json.loads(content)
    except json.JSONDecodeError:
        # 🔒 Safe fallback
        return {
            "intent": "recommendation",
            "rewritten_query": user_message,
            "product_type_filter": "single",
            "constraints": {
                "budget": None,
                "category": None,
                "preferences": []
            },
            "explicit_category": None
        }
