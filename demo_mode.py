import re
import random
import streamlit as st


# ============================================================
# BASIC HELPERS
# ============================================================

def get_case_text():
    return st.session_state.get("case_text", "") or ""


def clean_line(line):
    line = re.sub(r"\s+", " ", line)
    return line.strip()


def is_metadata_line(line):
    if not line:
        return True

    lower = line.lower().strip()

    patterns = [
        r"\b\d{2,4}-\d{2,4}-\d{2,4}\b",
        r"\brev:",
        r"copyright",
        r"president and fellows",
        r"harvard business school",
        r"to order copies",
        r"permissions",
        r"https?://",
        r"www\.",
        r"research associate",
    ]

    for pattern in patterns:
        if re.search(pattern, lower):
            return True

    if re.fullmatch(r"\d{1,3}", line):
        return True

    return False


def get_clean_lines(case_text):
    lines = []

    for raw_line in case_text.splitlines():

        line = clean_line(raw_line)

        if len(line) < 3:
            continue

        if is_metadata_line(line):
            continue

        lines.append(line)

    return lines


def get_case_body(case_text):
    """
    Remove obvious PDF headers, footers and exhibit fragments.
    """

    lines = get_clean_lines(case_text)

    body = []

    for line in lines:

        lower = line.lower()

        # Skip obvious exhibit/table fragments
        if re.match(
            r"^(exhibit|source:|note:|table)\b",
            lower
        ):
            continue

        # Skip lines dominated by financial-table numbers
        numbers = len(
            re.findall(
                r"\b\d+(?:\.\d+)?\b",
                line
            )
        )

        words = len(
            line.split()
        )

        if words > 0 and numbers >= 5 and numbers / words > 0.35:
            continue

        body.append(line)

    return body


def get_sentences(case_text):

    body = get_case_body(case_text)

    text = " ".join(body)

    sentences = re.split(
        r"(?<=[.!?])\s+",
        text
    )

    result = []

    for sentence in sentences:

        sentence = clean_line(sentence)

        if 50 <= len(sentence) <= 650:
            result.append(sentence)

    return result


def title_case(text):

    if not text:
        return ""

    if text.isupper():

        text = text.title()

        for word in [
            " In ",
            " Of ",
            " And ",
            " The ",
            " For ",
            " On ",
            " To "
        ]:
            text = text.replace(
                word,
                word.lower()
            )

    return text.strip()


# ============================================================
# TITLE
# ============================================================

def extract_title(case_text):

    lines = get_clean_lines(case_text)

    for line in lines[:80]:

        if re.search(
            r"\b(?:19|20)\d{2}\s*$",
            line
        ):

            if re.search(
                r"\bin\s+(?:19|20)\d{2}\s*$",
                line,
                re.IGNORECASE
            ):

                if len(line) <= 150:
                    return title_case(line)

    filename = st.session_state.get(
        "case_name",
        ""
    )

    if filename:

        filename = re.sub(
            r"\.(pdf|txt)$",
            "",
            filename,
            flags=re.IGNORECASE
        )

        filename = re.sub(
            r"\s*\(\d+\)\s*$",
            "",
            filename
        )

        filename = filename.replace(
            "_",
            " "
        )

        return clean_line(filename)

    return "Business Case"


# ============================================================
# COMPANY
# ============================================================

def extract_company(case_text):

    title = extract_title(case_text)

    match = re.match(
        r"^(.+?)\s+in\s+(?:19|20)\d{2}$",
        title,
        re.IGNORECASE
    )

    if match:

        company = match.group(1).strip()

        if 3 <= len(company) <= 100:
            return company

    lines = get_clean_lines(case_text)

    first_text = " ".join(
        lines[:100]
    )

    patterns = [
        r"\b([A-Z][A-Za-z0-9&.'-]*(?:\s+[A-Z][A-Za-z0-9&.'-]*){0,5})[’']s\b",
        r"\b([A-Z][A-Za-z0-9&.'-]*(?:\s+[A-Z][A-Za-z0-9&.'-]*){0,5})\s+(?:was|is|has|had|operates|manufactures|produces)\b"
    ]

    for pattern in patterns:

        matches = re.findall(
            pattern,
            first_text
        )

        for candidate in matches:

            candidate = clean_line(candidate)

            if candidate.lower() in [
                "the company",
                "this company",
                "the firm",
                "this firm",
                "the industry",
                "the market"
            ]:
                continue

            if len(candidate) >= 3:
                return candidate

    return "Not explicitly identified"


# ============================================================
# INDUSTRY
# ============================================================

def detect_industry(case_text):

    text = case_text.lower()

    categories = [
        (
            "Packaging / Containers",
            [
                "packaging",
                "containers",
                "cans",
                "bottles",
                "metal containers",
                "packaging equipment"
            ]
        ),
        (
            "Technology / Software",
            [
                "software",
                "technology",
                "saas",
                "cloud computing",
                "artificial intelligence"
            ]
        ),
        (
            "Banking / Financial Services",
            [
                "banking",
                "bank",
                "loan",
                "credit",
                "lending",
                "financial services"
            ]
        ),
        (
            "Retail",
            [
                "retail",
                "retailer",
                "stores",
                "store network"
            ]
        ),
        (
            "Healthcare / Pharmaceuticals",
            [
                "hospital",
                "healthcare",
                "pharmaceutical",
                "drug",
                "medical",
                "patient"
            ]
        ),
        (
            "Automotive",
            [
                "automotive",
                "automobile",
                "vehicle",
                "cars"
            ]
        ),
        (
            "Food & Beverage",
            [
                "food",
                "beverage",
                "restaurant",
                "drinks"
            ]
        ),
        (
            "Telecommunications",
            [
                "telecommunications",
                "telecom",
                "wireless network",
                "mobile network"
            ]
        ),
        (
            "Manufacturing / Industrial Products",
            [
                "manufacturing",
                "factory",
                "industrial",
                "production"
            ]
        )
    ]

    scores = []

    for category, keywords in categories:

        score = sum(
            text.count(keyword)
            for keyword in keywords
        )

        if score:
            scores.append(
                (score, category)
            )

    if not scores:
        return "Business / General Industry"

    scores.sort(
        reverse=True
    )

    return scores[0][1]


# ============================================================
# STRATEGIC PROBLEM DETECTION
# ============================================================

def problem_score(sentence):

    text = sentence.lower()

    score = 0

    # Strong strategic-problem indicators
    strong = [
        "challenge facing",
        "problem facing",
        "key challenge",
        "major challenge",
        "strategic challenge",
        "dilemma",
        "faced the challenge",
        "faced a challenge",
        "problem was",
        "challenge was",
        "question was"
    ]

    for phrase in strong:

        if phrase in text:
            score += 10

    # Management / strategy indicators
    strategy_words = [
        "strategy",
        "strategic",
        "management",
        "company",
        "firm",
        "business",
        "industry",
        "market",
        "competition",
        "competitive",
        "growth",
        "profit",
        "sales",
        "margin",
        "acquisition",
        "diversification",
        "expansion"
    ]

    score += sum(
        2
        for word in strategy_words
        if word in text
    )

    # Decision/problem indicators
    decision_words = [
        "should",
        "whether",
        "must",
        "need to",
        "needs to",
        "consider",
        "decide",
        "decision"
    ]

    score += sum(
        3
        for word in decision_words
        if word in text
    )

    # Penalize technical/product descriptions
    technical_words = [
        "oxygen",
        "carbonation",
        "polymer",
        "chemical",
        "material",
        "formula",
        "technical assistance",
        "plant"
    ]

    technical_count = sum(
        word in text
        for word in technical_words
    )

    strategic_count = sum(
        word in text
        for word in [
            "strategy",
            "strategic",
            "management",
            "market",
            "competition",
            "profit",
            "growth",
            "acquisition",
            "decision"
        ]
    )

    if technical_count >= 2 and strategic_count < 2:
        score -= 12

    return score


def extract_problem(case_text):

    sentences = get_sentences(case_text)

    ranked = []

    for sentence in sentences:

        score = problem_score(
            sentence
        )

        if score > 0:
            ranked.append(
                (score, sentence)
            )

    ranked.sort(
        key=lambda x: x[0],
        reverse=True
    )

    if ranked:

        return ranked[0][1]

    return (
        "The case requires management to determine "
        "how the company should respond to changing "
        "competitive, market and strategic conditions."
    )


# ============================================================
# KEY DECISION
# ============================================================

def decision_score(sentence):

    text = sentence.lower()

    score = 0

    if "whether" in text:
        score += 12

    if "should" in text:
        score += 8

    for word in [
        "decision",
        "consider",
        "bid",
        "acquire",
        "acquisition",
        "invest",
        "expand",
        "diversify",
        "enter",
        "strategy"
    ]:
        if word in text:
            score += 4

    for word in [
        "company",
        "management",
        "market",
        "business",
        "industry"
    ]:
        if word in text:
            score += 2

    return score


def extract_decision(case_text):

    sentences = get_sentences(case_text)

    ranked = []

    for sentence in sentences:

        score = decision_score(
            sentence
        )

        if score:
            ranked.append(
                (score, sentence)
            )

    ranked.sort(
        key=lambda x: x[0],
        reverse=True
    )

    if ranked:
        return ranked[0][1]

    return (
        "Management must determine which strategic "
        "course of action best addresses the case problem."
    )


# ============================================================
# IMPORTANT FACTS
# ============================================================

def fact_score(sentence):

    text = sentence.lower()

    # Strong business information
    business_terms = [
        "sales",
        "revenue",
        "profit",
        "profitability",
        "market share",
        "market",
        "industry",
        "competitor",
        "competition",
        "growth",
        "margin",
        "cost",
        "capital",
        "debt",
        "investment",
        "acquisition",
        "production",
        "customers"
    ]

    business_count = sum(
        word in text
        for word in business_terms
    )

    # Numbers
    number_count = len(
        re.findall(
            r"\b\d+(?:\.\d+)?%?\b",
            sentence
        )
    )

    score = (
        business_count * 3
        + number_count * 4
    )

    # Reject obvious table fragments
    words = sentence.split()

    if len(words) > 0:

        numeric_tokens = len(
            re.findall(
                r"\b\d+(?:\.\d+)?%?\b",
                sentence
            )
        )

        if numeric_tokens / len(words) > 0.30:
            score -= 15

    return score


def extract_facts(case_text):

    sentences = get_sentences(case_text)

    ranked = []

    for sentence in sentences:

        score = fact_score(
            sentence
        )

        if score > 4:
            ranked.append(
                (score, sentence)
            )

    ranked.sort(
        key=lambda x: x[0],
        reverse=True
    )

    facts = []

    for _, sentence in ranked:

        if sentence not in facts:

            facts.append(
                sentence
            )

        if len(facts) >= 6:
            break

    if not facts:

        facts = [
            "The case contains quantitative and qualitative evidence relevant to the strategic decision."
        ]

    return facts


# ============================================================
# STAKEHOLDERS
# ============================================================

def extract_stakeholders(case_text):

    text = case_text.lower()

    categories = [
        (
            "Senior management",
            [
                "ceo",
                "chief executive",
                "management",
                "executive"
            ]
        ),
        (
            "Customers",
            [
                "customer",
                "customers",
                "consumer",
                "consumers"
            ]
        ),
        (
            "Employees",
            [
                "employee",
                "employees",
                "workers",
                "workforce"
            ]
        ),
        (
            "Competitors",
            [
                "competitor",
                "competitors",
                "rival",
                "rivals"
            ]
        ),
        (
            "Investors / Shareholders",
            [
                "shareholder",
                "shareholders",
                "investor",
                "investors"
            ]
        ),
        (
            "Suppliers",
            [
                "supplier",
                "suppliers",
                "vendor",
                "vendors"
            ]
        ),
        (
            "Regulators",
            [
                "regulation",
                "regulator",
                "government",
                "compliance"
            ]
        )
    ]

    stakeholders = []

    for name, keywords in categories:

        if any(
            keyword in text
            for keyword in keywords
        ):
            stakeholders.append(name)

    if not stakeholders:

        stakeholders = [
            "Senior management",
            "Customers",
            "Employees",
            "Competitors"
        ]

    return stakeholders


# ============================================================
# ROOT CAUSES
# ============================================================

def extract_root_causes(case_text):

    text = case_text.lower()

    categories = [
        (
            "Competitive pressure",
            [
                "competitor",
                "competition",
                "rival",
                "market share"
            ]
        ),
        (
            "Market conditions",
            [
                "market",
                "industry",
                "demand",
                "customer"
            ]
        ),
        (
            "Cost or profitability pressure",
            [
                "cost",
                "profit",
                "margin",
                "expense"
            ]
        ),
        (
            "Growth requirements",
            [
                "growth",
                "expansion",
                "expand",
                "acquisition"
            ]
        ),
        (
            "Operational challenges",
            [
                "production",
                "manufacturing",
                "operations",
                "capacity"
            ]
        ),
        (
            "Strategic positioning",
            [
                "strategy",
                "strategic",
                "diversification",
                "position"
            ]
        )
    ]

    causes = []

    for name, keywords in categories:

        count = sum(
            text.count(keyword)
            for keyword in keywords
        )

        if count >= 2:
            causes.append(name)

    if not causes:

        causes = [
            "Competitive pressure",
            "Market conditions",
            "Strategic positioning"
        ]

    return causes[:5]


# ============================================================
# FRAMEWORKS
# ============================================================

def identify_frameworks(case_text):

    text = case_text.lower()

    frameworks = []

    if any(
        word in text
        for word in [
            "competitor",
            "competition",
            "rival",
            "market share"
        ]
    ):
        frameworks.append(
            "Porter's Five Forces"
        )

    if any(
        word in text
        for word in [
            "growth",
            "expansion",
            "new market",
            "new product",
            "diversification"
        ]
    ):
        frameworks.append(
            "Ansoff Matrix"
        )

    if any(
        word in text
        for word in [
            "strength",
            "weakness",
            "opportunity",
            "threat"
        ]
    ):
        frameworks.append(
            "SWOT Analysis"
        )

    if any(
        word in text
        for word in [
            "regulation",
            "regulatory",
            "government",
            "economic",
            "technology"
        ]
    ):
        frameworks.append(
            "PESTLE Analysis"
        )

    if not frameworks:

        frameworks = [
            "SWOT Analysis",
            "Porter's Five Forces",
            "Ansoff Matrix"
        ]

    return frameworks[:4]


# ============================================================
# TRADE-OFFS
# ============================================================

def identify_tradeoffs(case_text):

    text = case_text.lower()

    tradeoffs = []

    if any(
        word in text
        for word in [
            "growth",
            "expansion",
            "acquisition"
        ]
    ):
        tradeoffs.append(
            "Growth versus financial risk"
        )

    if any(
        word in text
        for word in [
            "cost",
            "profit",
            "margin"
        ]
    ):
        tradeoffs.append(
            "Investment versus profitability"
        )

    if any(
        word in text
        for word in [
            "competitor",
            "competition",
            "market share"
        ]
    ):
        tradeoffs.append(
            "Market share versus competitive risk"
        )

    if any(
        word in text
        for word in [
            "diversification",
            "new market",
            "new product"
        ]
    ):
        tradeoffs.append(
            "Diversification versus focus on the core business"
        )

    if not tradeoffs:

        tradeoffs = [
            "Short-term performance versus long-term growth",
            "Risk versus expected return",
            "Resource commitment versus strategic flexibility"
        ]

    return tradeoffs[:4]


# ============================================================
# OPTIONS
# ============================================================

def identify_options(case_text):

    text = case_text.lower()

    options = [
        "Strengthen the existing core business"
    ]

    if any(
        word in text
        for word in [
            "expansion",
            "expand",
            "new market"
        ]
    ):
        options.append(
            "Expand into attractive markets"
        )

    if any(
        word in text
        for word in [
            "acquisition",
            "acquire",
            "merger",
            "bid"
        ]
    ):
        options.append(
            "Pursue inorganic growth through acquisition or partnership"
        )

    if any(
        word in text
        for word in [
            "diversification",
            "new product"
        ]
    ):
        options.append(
            "Diversify into adjacent products or markets"
        )

    options.append(
        "Maintain the current strategy while improving execution"
    )

    return list(
        dict.fromkeys(options)
    )[:4]


# ============================================================
# MAIN DEMO ANALYSIS
# ============================================================

def get_demo_analysis():

    case_text = get_case_text()

    if not case_text:

        return """
1. CASE TITLE
Business Case

2. COMPANY / ORGANIZATION
Not identified.

3. INDUSTRY
Business / General Industry

4. CENTRAL PROBLEM
No case has been loaded.

5. KEY DECISION TO BE MADE
Upload a case study to begin analysis.

6. IMPORTANT FACTS
No case information available.

7. KEY STAKEHOLDERS
Not identified.

8. POSSIBLE ROOT CAUSES
Not identified.

9. RELEVANT BUSINESS FRAMEWORKS
SWOT Analysis
Porter's Five Forces
Ansoff Matrix

10. IMPORTANT DATA / NUMBERS
No case data available.

11. KEY TRADE-OFFS
Risk versus expected return.

12. INFORMATION THAT IS MISSING
Case information is required.

13. POTENTIAL STRATEGIC OPTIONS
Upload a case study before evaluating strategic options.
"""

    title = extract_title(case_text)
    company = extract_company(case_text)
    industry = detect_industry(case_text)
    problem = extract_problem(case_text)
    decision = extract_decision(case_text)
    facts = extract_facts(case_text)
    stakeholders = extract_stakeholders(case_text)
    causes = extract_root_causes(case_text)
    frameworks = identify_frameworks(case_text)
    tradeoffs = identify_tradeoffs(case_text)
    options = identify_options(case_text)

    facts_text = "\n".join(
        f"- {fact}"
        for fact in facts
    )

    stakeholders_text = "\n".join(
        f"- {item}"
        for item in stakeholders
    )

    causes_text = "\n".join(
        f"- {item}"
        for item in causes
    )

    frameworks_text = "\n".join(
        f"- {item}"
        for item in frameworks
    )

    tradeoffs_text = "\n".join(
        f"- {item}"
        for item in tradeoffs
    )

    options_text = "\n".join(
        f"- {item}"
        for item in options
    )

    return f"""
1. CASE TITLE
{title}

2. COMPANY / ORGANIZATION
{company}

3. INDUSTRY
{industry}

4. CENTRAL PROBLEM
{problem}

5. KEY DECISION TO BE MADE
{decision}

6. IMPORTANT FACTS
{facts_text}

7. KEY STAKEHOLDERS
{stakeholders_text}

8. POSSIBLE ROOT CAUSES
{causes_text}

9. RELEVANT BUSINESS FRAMEWORKS
{frameworks_text}

10. IMPORTANT DATA / NUMBERS
The case contains quantitative evidence that should be evaluated before making the final recommendation.

11. KEY TRADE-OFFS
{tradeoffs_text}

12. INFORMATION THAT IS MISSING
- Some strategic outcomes may require assumptions because the case does not provide every piece of information.
- Additional financial or competitive information may be useful for validating the decision.

13. POTENTIAL STRATEGIC OPTIONS
{options_text}
"""


# ============================================================
# SOCRATIC COACH
# ============================================================

def get_demo_coaching_question():

    questions = [
        "What do you believe is the central business problem, and which evidence from the case supports your view?",
        "What is the most important decision management has to make?",
        "Which assumption in your current thinking is most important to test?",
        "What are the strongest alternatives available to management?",
        "Which piece of evidence most strongly supports your preferred strategy?",
        "What is the biggest risk to your recommendation?"
    ]

    return random.choice(questions)


def get_demo_coaching_feedback():

    return """
STRENGTH:
You have identified a reasonable direction for the case.

IMPROVEMENT:
Connect your conclusion more explicitly to specific evidence from the case.

SCORE:
6/10
"""


# ============================================================
# FRAMEWORK LAB
# ============================================================

def get_demo_framework_recommendation():

    frameworks = identify_frameworks(
        get_case_text()
    )

    output = []

    for framework in frameworks[:3]:

        output.append(
            f"""
{framework}

Why it is relevant:
Use this framework to structure the strategic factors influencing the case.

What to investigate:
Identify the strongest evidence, assess the implications and connect the analysis to the decision.
"""
        )

    return (
        "\n".join(output)
        +
        f"""

RECOMMENDED FRAMEWORK
{frameworks[0]}
"""
    )


def get_demo_framework_feedback():

    return """
STRENGTH:
Your framework provides a useful structure for organizing the case evidence.

MISSING:
Connect the individual factors more clearly to the strategic decision.

CHALLENGE:
Which factor would change your recommendation the most if its underlying assumption changed?

SCORE:
6/10
"""


# ============================================================
# DEVIL'S ADVOCATE
# ============================================================

def get_demo_devil_feedback():

    return """
KEY ASSUMPTION:
Your recommendation assumes that the expected benefits outweigh the implementation risks.

CHALLENGE:
What evidence proves that assumption?

ALTERNATIVE VIEW:
Management could prioritize strengthening the existing business rather than pursuing the proposed strategy.

FOLLOW-UP QUESTION:
What would have to be true for the alternative strategy to be superior?
"""


# ============================================================
# STRESS TEST
# ============================================================

def get_demo_stress_test():

    scenarios = [
        {
            "scenario":
                "The company's available investment budget is reduced by 30%.",
            "impact":
                "A capital-intensive strategy may become less feasible."
        },
        {
            "scenario":
                "Marketing and operating costs increase by 25%.",
            "impact":
                "The expected financial attractiveness of the strategy may decline."
        },
        {
            "scenario":
                "A major competitor enters the target market.",
            "impact":
                "Competitive pressure may reduce the expected benefits of the strategy."
        },
        {
            "scenario":
                "Demand in the target market is 20% lower than expected.",
            "impact":
                "Expected revenue and return on investment may decline."
        },
        {
            "scenario":
                "The implementation timeline is shortened by 40%.",
            "impact":
                "The organization may have insufficient time and resources to execute the original strategy."
        }
    ]

    return random.choice(scenarios)


def get_demo_stress_feedback():

    return """
STRENGTH:
You recognized that the changed business condition requires an adjustment to the original strategy.

MISSING:
Quantify the impact of the shock where possible and explain which part of the recommendation should change.

CHALLENGE:
Would your recommendation still create value under the new condition?

SCORE:
6/10
"""