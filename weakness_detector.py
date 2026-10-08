def detect_weaknesses(scores):

    if not scores:
        return {
            "strongest": "Not enough data",
            "weakest": "Not enough data",
            "insight": "Complete more coaching activities to identify your strengths and weaknesses."
        }

    average = sum(scores) / len(scores)

    if average >= 8:
        strongest = "Strategic Reasoning"
    elif average >= 6:
        strongest = "Problem Understanding"
    else:
        strongest = "Problem Identification"

    if average < 4:
        weakest = "Evidence Usage"
        insight = (
            "You need to strengthen your use of case evidence. "
            "Support strategic claims with specific numbers, facts "
            "and trends from the case."
        )

    elif average < 6:
        weakest = "Logical Reasoning"
        insight = (
            "Your answers show the right direction but need stronger "
            "logic connecting evidence to your conclusion."
        )

    elif average < 8:
        weakest = "Trade-off Analysis"
        insight = (
            "Your reasoning is developing. Focus more on comparing "
            "alternatives, risks and trade-offs before recommending "
            "a strategy."
        )

    else:
        weakest = "Advanced Strategic Thinking"
        insight = (
            "Your overall reasoning is strong. Focus on deeper "
            "trade-offs, implementation risks and quantitative justification."
        )

    return {
        "strongest": strongest,
        "weakest": weakest,
        "insight": insight
    }