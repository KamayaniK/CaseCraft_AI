from ai_router import generate_ai_response


def generate_challenge(
    case_text,
    student_recommendation
):

    prompt = f"""
You are the Devil's Advocate in an MBA case analysis.

CASE:
{case_text}

STUDENT'S RECOMMENDATION:
{student_recommendation}

Challenge the student's recommendation.

Do NOT give the correct answer.

Generate:

1. KEY ASSUMPTION
2. CHALLENGE
3. ALTERNATIVE VIEW
4. FOLLOW-UP QUESTION

Keep the response concise and business-focused.
"""

    return generate_ai_response(prompt)