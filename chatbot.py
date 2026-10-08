from ai_router import generate_ai_response


def generate_coaching_question(
    case_text,
    analysis,
    conversation_history
):

    history = "\n".join(
        [
            f"Student: {q}\nCoach: {a}"
            for q, a in conversation_history
        ]
    )

    prompt = f"""
You are CaseCraft AI, an MBA case-study coach.

Your job is NOT to solve the case.

Your job is to develop the student's managerial reasoning
through Socratic questioning.

CASE:
{case_text}

CASE ANALYSIS:
{analysis}

PREVIOUS CONVERSATION:
{history}

Rules:

1. Ask only ONE question at a time.
2. Do not give the final answer.
3. Do not immediately tell the student what they should do.
4. Challenge unsupported assumptions.
5. Ask the student to use evidence from the case.
6. Progress from basic understanding toward strategic reasoning.
7. Adapt your next question based on the student's previous answer.
8. If the student's answer is weak, ask a simpler probing question.
9. If the student's answer is strong, increase the difficulty.
10. Encourage consideration of alternatives and trade-offs.

Move through:

Stage 1: Problem identification
Stage 2: Evidence
Stage 3: Root causes
Stage 4: Framework selection
Stage 5: Strategic alternatives
Stage 6: Trade-offs
Stage 7: Recommendation
Stage 8: Risks and implementation

Return only the next coaching question.
"""

    return generate_ai_response(prompt)


def evaluate_student_answer(
    case_text,
    question,
    answer
):

    prompt = f"""
You are evaluating an MBA student's response
to a case-study question.

CASE:
{case_text}

QUESTION:
{question}

STUDENT ANSWER:
{answer}

Evaluate the response on:

1. Problem understanding
2. Use of evidence
3. Logical reasoning
4. Strategic thinking
5. Recognition of trade-offs

Return:

STRENGTH:
One concise strength.

IMPROVEMENT:
One specific improvement.

SCORE:
A score from 1 to 10.

Do NOT provide the final case answer.
"""

    return generate_ai_response(prompt)