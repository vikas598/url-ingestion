from openai import OpenAI
import os

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
MODEL = "gpt-4o-mini"

def generate_small_talk_response(user_message: str) -> str:
    system_prompt = (
        "You are a friendly AI assistant for Millex. "
        "Respond naturally and briefly. "
        "Do not mention products unless the user asks."
    )

    response = client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message}
        ],
        temperature=0.7
    )

    return response.choices[0].message.content.strip()
