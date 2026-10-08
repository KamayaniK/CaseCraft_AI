import re


def extract_score(evaluation):
    """
    Extract the score from AI feedback.
    Handles formats such as:
    SCORE: 7/10
    SCORE: 7 / 10
    **SCORE:** 7/10
    SCORE - 7/10
    """

    if not evaluation:
        return None

    patterns = [
        r"SCORE\s*[:\-]?\s*\**\s*(\d+(?:\.\d+)?)\s*/\s*10",
        r"SCORE\s*[:\-]?\s*(\d+(?:\.\d+)?)",
    ]

    for pattern in patterns:

        match = re.search(
            pattern,
            evaluation,
            re.IGNORECASE
        )

        if match:
            return float(match.group(1))

    return None


def calculate_score(scores):

    valid_scores = [
        score for score in scores
        if score is not None
    ]

    if not valid_scores:
        return 0

    return round(
        sum(valid_scores) / len(valid_scores),
        1
    )


def performance_label(score):

    if score >= 9:
        return "Exceptional"

    elif score >= 8:
        return "Strong"

    elif score >= 7:
        return "Developing"

    elif score >= 6:
        return "Needs Improvement"

    return "Needs Significant Improvement"