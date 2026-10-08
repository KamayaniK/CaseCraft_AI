import random

from ai_router import generate_ai_response


def generate_stress_test():

    scenarios = [
        {
            "scenario": "The company's available investment budget is reduced by 30%.",
            "impact": "A capital-intensive strategy may become less feasible."
        },
        {
            "scenario": "Marketing costs increase by 25%.",
            "impact": "The financial attractiveness of the recommended strategy may decrease."
        },
        {
            "scenario": "A major competitor enters the target market.",
            "impact": "Competitive pressure may reduce the expected benefits of the strategy."
        },
        {
            "scenario": "Demand in the target market is 20% lower than expected.",
            "impact": "Expected revenue and return on investment may decline."
        },
        {
            "scenario": "The company's implementation timeline is shortened by 40%.",
            "impact": "The organization may not have enough time or resources to execute the original strategy effectively."
        },
        {
            "scenario": "A new regulation increases compliance costs significantly.",
            "impact": "The strategy may become less profitable and require operational changes."
        }
    ]

    return random.choice(scenarios)


def evaluate_stress_test(case_text, scenario, student_response):

    prompt = f"""
You are an MBA strategy professor evaluating a student's
response to a business stress-test scenario.

CASE:
{case_text}

BUSINESS SHOCK:
{scenario}

STUDENT RESPONSE:
{student_response}

Evaluate whether the student appropriately adapted
their recommendation to the changed business condition.

Assess:

1. Understanding of the business shock
2. Ability to adapt the strategy
3. Recognition of financial/operational implications
4. Strategic reasoning
5. Recognition of risks and trade-offs

Return exactly:

STRENGTH:
One specific strength.

MISSING:
One important consideration the student missed.

CHALLENGE:
One question that would make the student think deeper.

SCORE:
A score from 1 to 10.

Do not provide the complete case solution.
"""

    return generate_ai_response(prompt)