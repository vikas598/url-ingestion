import os
import re
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

MODEL = "gpt-4o-mini"


def _extract_weight_in_grams(title: str) -> float | None:
    """Extract weight from title and convert to grams."""
    match = re.search(r'(\d+(?:\.\d+)?)\s*(g|kg|gm|gram|grams)', title.lower())
    if match:
        value = float(match.group(1))
        unit = match.group(2)
        if unit in ['kg', 'kgs']:
            return value * 1000
        return value
    return None


def generate_recommendation(
    user_message: str,
    intent_data: dict,
    products: list[dict],
    history: list = None
) -> str:
    """
    Uses LLM to reason over retrieved products and generate a structured response.
    """

    # Format History
    history_context = ""
    if history:
        history_context = "Conversation History (for context):\n"
        for msg in history[-5:]:
            role = msg.get("role", "unknown")
            content = msg.get("content", "")
            history_context += f"- {role.upper()}: {content}\n"
        history_context += "\n"

    if not products:
        # Check if it's a general question not needing products
        if intent_data.get('intent') in ['info', 'small_talk'] and history:
             # Let LLM answer based on history if no products needed
             pass
        else:
            return (
                "I couldn't find any products that match your requirement. "
                "Would you like to adjust your preferences?"
            )

    # Build Product Context (Flat List)
    product_context = []
    
    for i, p in enumerate(products, start=1):
        # 1. Price
        price_info = "N/A"
        price = 0
        if p.get('pricing', {}).get('price'):
            price = float(p['pricing']['price'])
            price_info = f"₹{price}"
        elif p.get('variants'):
            # Get lowest variant price
            prices = [float(v.get('price', 0) or 0) for v in p['variants'] if v.get('price')]
            if prices:
                price = min(prices)
                price_info = f"₹{price}"
        
        # 2. Description Truncation (for context only, output controls display)
        description = p.get('description', '').strip()
        
        # 3. Format for LLM
        product_info = f"Product ID: {p.get('product_id')}\n"
        product_info += f"Name: {p.get('title', 'Unknown')}\n"
        product_info += f"Price: {price_info}\n"
        product_info += f"Full Description: {description}\n"
        product_info += "-" * 20
        
        product_context.append(product_info)

    product_block = "\n".join(product_context)

    system_prompt = (
        "You are an expert e-commerce advisor for Millex (Millet-based products).\n"
        "Your goal is to help users choose the best product for their specific needs based on the provided product list.\n\n"
        
        "### CRITICAL INSTRUCTIONS:\n"
        "1. **RELEVANCE FILTER (MOST IMPORTANT)**: ONLY show products that are DIRECTLY relevant to what the user asked for. "
        "If the user asks for 'Idli', ONLY show Idli-related products. Do NOT pad the response with unrelated products like 'Health Mix' or 'Dosa Mix'. "
        "If only 1 product matches the user's request, show ONLY that 1 product. There is NO compulsion to show multiple products.\n"
        "2. **Analyze Descriptions**: Read the 'Full Description' of each product you decide to show. Based on the description, YOU decide the best Category/Group name. Do NOT use hardcoded categories.\n"
        "3. **Response Format**: For each product, use EXACTLY this format:\n"
        "   [Product Name] - [Price]\n"
        "   [Short Description: Max 1-2 lines. Focus on key benefits relative to the user's request.]\n\n"
        
        "### RULES:\n"
        "- If the user asks for a specific product (e.g., 'Idli') and you found a matching VARIANT (e.g., 'Millet Rava Idli'), present it DIRECTLY. Do NOT apologize.\n"
        "- If the user asks for 'Idli' and you found NOTHING resembling Idli, then state you couldn't find it and offer alternatives.\n"
        "- **Combo vs Single**: If the user specifically asked for 'Single' but you found 'Combos', or vice versa, mention this mismatch briefly.\n"
        "- **Comparison**: ONLY add a 'Which should you choose?' section if you are showing 2+ RELEVANT products. If showing only 1 product, OMIT this section.\n"
        "- **COMBO UPSELL**: If you are showing single products, ALWAYS end with:\n"
        "   'Tip: We also have combo packs that include [product name]. Would you like to see them?'\n"
        "- **Visual Selection**: At the very end, output `[SELECTED_IDS: id1, id2, ...]` containing ONLY the IDs of products you actually showed.\n"
    )

    user_prompt = f"""
{history_context}
User Question: "{user_message}"

Product Data:
{product_block}

Task:
Categorize and recommend the products using the requested format.
"""

    response = client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        temperature=0.3
    )

    content = response.choices[0].message.content.strip()
    
    # Parse Selected IDs
    selected_ids = []
    match = re.search(r'\[SELECTED_IDS:(.*?)\]', content, re.DOTALL)
    if match:
        id_str = match.group(1).strip()
        if id_str:
            # Split by comma or whitespace
            selected_ids = [pid.strip() for pid in re.split(r'[,\s]+', id_str) if pid.strip()]
        
        # Remove the tag from the final response text
        content = content.replace(match.group(0), "").strip()
        
    if not match and products:
        selected_ids = [p.get('product_id') for p in products]

    return content, selected_ids


def generate_catalog_summary(user_message: str) -> str:
    """
    Loads ALL products from vector store metadata and generates
    a formatted summary of the entire Millex catalog.
    """
    from pathlib import Path
    import json

    META_PATH = Path(__file__).resolve().parent.parent / "recommender_system" / "vector_store" / "products_meta.json"

    if not META_PATH.exists():
        return "I'm sorry, I couldn't load the product catalog right now. Please try again later."

    with open(META_PATH, "r", encoding="utf-8") as f:
        all_products = json.load(f)

    if not all_products:
        return "The product catalog is currently empty."

    # Build compact product list for LLM
    product_lines = []
    for p in all_products:
        title = p.get("title", "Unknown")
        product_type = p.get("product_type", "single")
        price = p.get("pricing", {}).get("price")
        price_str = f"₹{price}" if price else "Price on request"
        categories = p.get("category", [])
        cat_str = ", ".join(categories) if categories else "General"
        in_stock = "In Stock" if p.get("availability", {}).get("in_stock") else "Out of Stock"

        product_lines.append(f"- {title} | {product_type} | {price_str} | {cat_str} | {in_stock}")

    catalog_block = "\n".join(product_lines)

    system_prompt = (
        "You are Millex's friendly AI assistant. The user is asking about the website/brand.\n"
        "You have access to the FULL product catalog below.\n\n"
        "Generate a well-formatted, engaging summary of the Millex store that includes:\n"
        "1. A brief intro about Millex (millet-based health products)\n"
        "2. Product categories available (group them logically)\n"
        "3. Price range overview\n"
        "4. A closing line inviting the user to explore or ask for recommendations\n\n"
        "Keep it concise but informative. Use markdown formatting (headers, bullet points).\n"
        "Do NOT list every single product individually — group and summarize them.\n"
    )

    user_prompt = f"""
User Question: "{user_message}"

Full Product Catalog ({len(all_products)} products):
{catalog_block}

Generate a formatted overview of the Millex store based on this data.
"""

    response = client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        temperature=0.5
    )

    return response.choices[0].message.content.strip()
