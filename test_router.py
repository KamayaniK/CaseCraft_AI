from ai_router import generate_ai_response, get_last_provider

prompt = """
You are testing the CaseCraft AI system.

Reply with exactly:

CaseCraft AI router test successful.
"""

try:
    response = generate_ai_response(prompt)

    print("\nAI RESPONSE:")
    print(response)

    print("\nPROVIDER USED:")
    print(get_last_provider())

except Exception as error:
    print("\nALL PROVIDERS FAILED:")
    print(error)