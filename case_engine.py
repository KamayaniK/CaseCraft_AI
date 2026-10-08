import os
from pypdf import PdfReader
from dotenv import load_dotenv
from ai_router import generate_ai_response

load_dotenv()


def extract_case_text(uploaded_file):
    """Extract text from an uploaded PDF or TXT file."""

    if uploaded_file.name.lower().endswith(".pdf"):
        reader = PdfReader(uploaded_file)

        text = ""

        for page in reader.pages:
            page_text = page.extract_text()

            if page_text:
                text += page_text + "\n"

        return text.strip()

    elif uploaded_file.name.lower().endswith(".txt"):
        return uploaded_file.read().decode("utf-8")

    return ""


def analyze_case(case_text):

    prompt = f"""
You are an MBA case-analysis expert.

Analyze the following business case.

CASE:
{case_text}

Return the analysis in exactly these sections:

1. CASE TITLE
2. COMPANY / ORGANIZATION
3. INDUSTRY
4. CENTRAL PROBLEM
5. KEY DECISION TO BE MADE
6. IMPORTANT FACTS
7. KEY STAKEHOLDERS
8. POSSIBLE ROOT CAUSES
9. RELEVANT BUSINESS FRAMEWORKS
10. IMPORTANT DATA / NUMBERS
11. KEY TRADE-OFFS
12. INFORMATION THAT IS MISSING
13. POTENTIAL STRATEGIC OPTIONS

Important:
- Do not solve the case.
- Do not provide a final recommendation.
- Identify what the student needs to analyze.
- Clearly distinguish facts from assumptions.
"""

    return generate_ai_response(prompt)