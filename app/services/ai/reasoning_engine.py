import os
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

MODEL = "gpt-4o-mini"


def generate_recommendation(
    user_message: str,
    intent_data: dict,
    products: list[dict]
) -> str:
    """
    Uses LLM to reason over retrieved products and generate a user-facing response.
    """

    if not products:
        return (
            "I couldn’t find any products that match your requirement. "
            "Would you like to adjust your preferences?"
        )

    # Format product context safely
    product_context = []
    for i, p in enumerate(products, start=1):
        product_context.append(
            f"{i}. {p.get('title', 'Unknown')} – {p.get('source_url', '')}"
        )

    product_block = "\n".join(product_context)

    system_prompt = (
        "You are an AI shopping assistant.\n"
        "Rules:\n"
        "- You can ONLY use the products provided to you.\n"
        "- Do NOT invent or assume other products.\n"
        "- Compare products honestly based on the data.\n"
        "- Be concise, helpful, and user-focused.\n"
        "- If no product fits well, say so."
    )

    user_prompt = f"""
User message:
"{user_message}"

Intent data:
{intent_data}

Available products:
{product_block}

Task:
- Recommend the best option(s)
- Explain WHY they fit the user
- Ask one helpful follow-up question OR suggest next action
"""

    response = client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        temperature=0.4
    )

    return response.choices[0].message.content.strip()
