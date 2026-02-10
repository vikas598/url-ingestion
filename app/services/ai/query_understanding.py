import json
import os
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

MODEL = "gpt-4o-mini"


def extract_query_intent(user_message: str) -> dict:
    """
    Uses LLM to rewrite query and extract intent + constraints.
    Returns structured dict.
    """

    system_prompt = (
        "You are an AI assistant that converts user shopping queries into structured search data.\n"
        "Rules:\n"
        "- Do NOT invent products\n"
        "- Do NOT answer the user\n"
        "- Only return valid JSON\n"
        "- Keep rewritten_query short and optimized for semantic search"
    )

    user_prompt = f"""
User message:
"{user_message}"

Return JSON with:
- rewritten_query (string)
- intent (one of: recommendation, comparison, info, buy)
- constraints:
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
        # Hard fallback — never break the pipeline
        return {
            "rewritten_query": user_message,
            "intent": "recommendation",
            "constraints": {
                "budget": None,
                "category": None,
                "preferences": []
            },
            "explicit_category": None
        }
