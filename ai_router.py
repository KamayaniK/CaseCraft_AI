import os
import requests
from dotenv import load_dotenv
from groq import Groq
from google import genai

load_dotenv()


# ============================================================
# CONFIGURATION
# ============================================================

GROQ_MODEL = "openai/gpt-oss-120b"
GEMINI_MODEL = "gemini-3.8-flash"
OPENROUTER_MODEL = "openrouter/free"

_last_provider = None


# ============================================================
# PROVIDER STATUS
# ============================================================

def get_last_provider():
    return _last_provider


# ============================================================
# GROQ
# ============================================================

def call_groq(prompt):
    api_key = os.getenv("GROQ_API_KEY")

    if not api_key:
        raise Exception("GROQ_API_KEY not found")

    client = Groq(api_key=api_key)

    response = client.chat.completions.create(
        model=GROQ_MODEL,
        messages=[
            {
                "role": "user",
                "content": prompt
            }
        ],
        temperature=0.3
    )

    return response.choices[0].message.content.strip()


# ============================================================
# GEMINI
# ============================================================

def call_gemini(prompt):
    api_key = os.getenv("GEMINI_API_KEY")

    if not api_key:
        raise Exception("GEMINI_API_KEY not found")

    client = genai.Client(api_key=api_key)

    response = client.models.generate_content(
        model=GEMINI_MODEL,
        contents=prompt
    )

    return response.text.strip()


# ============================================================
# OPENROUTER
# ============================================================

def call_openrouter(prompt):
    api_key = os.getenv("OPENROUTER_API_KEY")

    if not api_key:
        raise Exception("OPENROUTER_API_KEY not found")

    url = "https://openrouter.ai/api/v1/chat/completions"

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }

    payload = {
        "model": OPENROUTER_MODEL,
        "messages": [
            {
                "role": "user",
                "content": prompt
            }
        ],
        "temperature": 0.3
    }

    response = requests.post(
        url,
        headers=headers,
        json=payload,
        timeout=60
    )

    if response.status_code != 200:
        raise Exception(
            f"OpenRouter error {response.status_code}: "
            f"{response.text}"
        )

    data = response.json()

    return data["choices"][0]["message"]["content"].strip()


# ============================================================
# CENTRAL AI ROUTER
# ============================================================

def generate_ai_response(prompt):
    """
    Provider priority:

    1. Groq
    2. Gemini
    3. OpenRouter

    If one provider fails, automatically move
    to the next provider.
    """

    global _last_provider

    providers = [
        ("Groq", call_groq),
        ("Gemini", call_gemini),
        ("OpenRouter", call_openrouter)
    ]

    errors = []

    for provider_name, provider_function in providers:

        try:
            result = provider_function(prompt)

            if result:
                _last_provider = provider_name
                return result

        except Exception as error:
            errors.append(
                f"{provider_name}: {str(error)}"
            )
            continue

    _last_provider = None

    raise Exception(
        "All AI providers failed.\n\n"
        + "\n".join(errors)
    )