from ai_router import generate_ai_response


def recommend_framework(case_text):

    prompt = f"""
You are an MBA strategy professor.

Analyze this business case:

{case_text}

Choose the THREE most appropriate strategic frameworks from:

- SWOT Analysis
- Porter's Five Forces
- PESTLE Analysis
- Ansoff Matrix
- 4Ps Marketing Mix
- BCG Matrix

For each selected framework provide:

1. Framework name
2. Why it is relevant
3. What the student should investigate

Then identify ONE framework as:

RECOMMENDED FRAMEWORK

Do not solve the case.
Do not provide a final recommendation.
"""

    return generate_ai_response(prompt)


def evaluate_framework(
    case_text,
    framework,
    student_analysis
):

    prompt = f"""
You are an MBA strategy professor evaluating
a student's framework analysis.

CASE:
{case_text}

FRAMEWORK:
{framework}

STUDENT'S ANALYSIS:
{student_analysis}

Evaluate:

1. Relevance to the case
2. Correct use of the framework
3. Use of case evidence
4. Depth of analysis
5. Strategic insight

Return:

STRENGTH:
One specific strength.

MISSING:
One important factor the student missed.

CHALLENGE:
One question that would make the student think deeper.

SCORE:
Score from 1 to 10.

Do not solve the case.
"""

    return generate_ai_response(prompt)