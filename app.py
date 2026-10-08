"""
CaseCraft AI - MBA Case Reasoning Simulator (Streamlit front end)

Design notes
------------
* Theme-proof: the app does not depend on Streamlit's light/dark theme.
  Every card, label, tab, input and button is styled explicitly, and all
  model output is rendered through our own HTML cards. (The earlier
  version showed invisible text because Streamlit was in dark mode while
  the page background was forced to light.)
* HTML snippets are flattened by render_html() so Markdown never turns
  them into code blocks.
* Errors stay on screen: the app only reruns after a successful call.
* Guardrails: input validation, prompt-injection filter, empty-output
  rejection, demo/offline fallback.

Your other modules (case_engine, chatbot, framework_lab, devils_advocate,
stress_test, scoring, weakness_detector, case_map) are used unchanged.
"""

import copy
import html
import re

import plotly.graph_objects as go
import streamlit as st

from case_engine import extract_case_text, analyze_case
from chatbot import generate_coaching_question, evaluate_student_answer
from framework_lab import recommend_framework, evaluate_framework
from devils_advocate import generate_challenge
from stress_test import generate_stress_test, evaluate_stress_test
from scoring import extract_score, calculate_score, performance_label
from weakness_detector import detect_weaknesses
from case_map import create_case_map


# ============================================================
# PAGE CONFIG
# ============================================================

st.set_page_config(
    page_title="CaseCraft AI",
    page_icon="◆",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ============================================================
# CSS  (theme-proof: works in Streamlit light AND dark mode)
# ============================================================

# Everything in the main area, i.e. not the sidebar.
MAIN = '[data-testid="stAppViewContainer"] > :not([data-testid="stSidebar"])'

CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap');

/* ---------- BASE ---------- */

.stApp {
    background-color: #F4F6FA;
    color: #1E293B;
}

header[data-testid="stHeader"] {
    background: transparent;
}

header[data-testid="stHeader"] * {
    color: #475569 !important;
}

.main .block-container,
[data-testid="stMainBlockContainer"] {
    padding-top: 1.4rem;
    padding-bottom: 3rem;
    max-width: 1320px;
}

[data-testid="stMarkdownContainer"],
[data-testid="stMarkdownContainer"] * {
    font-family: 'Plus Jakarta Sans', 'Segoe UI', system-ui, sans-serif;
}

/* ---------- FORCE READABLE TEXT IN MAIN AREA ---------- */

@MAIN p,
@MAIN li,
@MAIN label,
@MAIN h1, @MAIN h2, @MAIN h3, @MAIN h4, @MAIN h5, @MAIN h6 {
    color: #1E293B !important;
    font-family: 'Plus Jakarta Sans', 'Segoe UI', system-ui, sans-serif;
}

@MAIN [data-testid="stMarkdownContainer"] {
    color: #1E293B;
}

/* ---------- SIDEBAR ---------- */

[data-testid="stSidebar"] {
    background-color: #0F172A;
}

[data-testid="stSidebar"] * {
    color: #F8FAFC;
}

[data-testid="stSidebar"] hr {
    border-color: #1E293B;
}

[data-testid="stFileUploaderDropzone"] {
    background-color: #1E293B;
    border: 1px dashed #475569;
}

[data-testid="stFileUploaderDropzone"] * {
    color: #E2E8F0 !important;
}

[data-testid="stFileUploaderDropzone"] button {
    background-color: #2563EB;
    border: none;
}

.side-brand {
    font-size: 1.3rem;
    font-weight: 800;
}

.side-tagline {
    font-size: 0.8rem;
    color: #94A3B8 !important;
}

.side-section {
    font-size: 0.82rem;
    font-weight: 700;
    color: #94A3B8 !important;
    margin-bottom: 4px;
}

.side-note {
    font-size: 0.76rem;
    line-height: 1.65;
    color: #94A3B8 !important;
}

.side-note b {
    color: #E2E8F0 !important;
}

/* ---------- APP BAR ---------- */

.appbar {
    display: flex;
    justify-content: space-between;
    align-items: center;
    gap: 16px;
    background: #0F172A;
    border-radius: 16px;
    padding: 16px 22px;
    margin-bottom: 18px;
}

.appbar-left {
    display: flex;
    align-items: center;
    gap: 14px;
}

.appbar-right {
    display: flex;
    align-items: center;
    gap: 10px;
    flex-wrap: wrap;
    justify-content: flex-end;
}

.logo {
    width: 40px;
    height: 40px;
    border-radius: 11px;
    background: #2563EB;
    color: #FFFFFF;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 1.15rem;
    font-weight: 800;
}

.appbar-title {
    color: #FFFFFF;
    font-size: 1.25rem;
    font-weight: 800;
    line-height: 1.2;
}

.appbar-sub {
    color: #94A3B8;
    font-size: 0.82rem;
}

.pill {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    border-radius: 999px;
    padding: 5px 13px;
    font-size: 0.78rem;
    font-weight: 700;
}

.pill.live {
    background: rgba(34, 197, 94, 0.16);
    color: #4ADE80;
}

.pill.demo {
    background: rgba(245, 158, 11, 0.18);
    color: #FBBF24;
}

.pill.case {
    background: rgba(148, 163, 184, 0.18);
    color: #E2E8F0;
    max-width: 340px;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
}

/* ---------- GENERIC CARDS ---------- */

.card {
    background: #FFFFFF;
    border: 1px solid #E2E8F0;
    border-radius: 14px;
    padding: 18px 22px;
    margin-bottom: 16px;
}

.case-name-label {
    color: #64748B;
    font-size: 0.82rem;
    font-weight: 650;
}

.case-name {
    font-size: 1.2rem;
    font-weight: 750;
    color: #0F172A;
    margin-top: 2px;
}

.case-meta {
    color: #64748B;
    font-size: 0.85rem;
    margin-top: 4px;
}

.section-heading {
    font-size: 1.2rem;
    font-weight: 750;
    color: #0F172A;
    margin: 6px 0 10px 0;
}

.muted {
    color: #64748B;
    font-size: 0.92rem;
    line-height: 1.55;
    margin: 2px 0 14px 0;
}

.footer {
    text-align: center;
    color: #94A3B8;
    font-size: 0.78rem;
    padding: 36px 0 8px;
}

/* ---------- KPI CARDS ---------- */

.kpi {
    background: #FFFFFF;
    border: 1px solid #E2E8F0;
    border-top: 3px solid #2563EB;
    border-radius: 14px;
    padding: 16px 20px;
    min-height: 112px;
}

.kpi.green { border-top-color: #16A34A; }
.kpi.amber { border-top-color: #D97706; }
.kpi.violet { border-top-color: #7C3AED; }

.kpi-label {
    color: #64748B;
    font-size: 0.85rem;
    font-weight: 650;
}

.kpi-value {
    color: #0F172A;
    font-size: 1.75rem;
    font-weight: 800;
    margin-top: 6px;
}

.kpi-sub {
    color: #94A3B8;
    font-size: 0.8rem;
    margin-top: 2px;
}

/* ---------- STEPPER ---------- */

.stepper {
    display: flex;
    align-items: center;
    background: #FFFFFF;
    border: 1px solid #E2E8F0;
    border-radius: 14px;
    padding: 14px 22px;
    margin: 2px 0 16px 0;
    overflow-x: auto;
}

.step {
    display: flex;
    align-items: center;
    gap: 10px;
    white-space: nowrap;
}

.dot {
    width: 26px;
    height: 26px;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 0.8rem;
    font-weight: 700;
    background: #E2E8F0;
    color: #64748B;
}

.step.done .dot { background: #16A34A; color: #FFFFFF; }
.step.current .dot { background: #2563EB; color: #FFFFFF; }

.step-name {
    font-size: 0.9rem;
    font-weight: 600;
    color: #64748B;
}

.step.done .step-name,
.step.current .step-name {
    color: #0F172A;
}

.step-line {
    flex: 1;
    height: 2px;
    background: #E2E8F0;
    margin: 0 14px;
    min-width: 24px;
}

.step-line.done { background: #16A34A; }

/* ---------- LANDING ---------- */

.welcome-card {
    background: #FFFFFF;
    border: 1px solid #E2E8F0;
    border-radius: 18px;
    padding: 44px 40px;
    text-align: center;
    margin-bottom: 18px;
}

.welcome-title {
    font-size: 2rem;
    font-weight: 800;
    color: #0F172A;
    margin-bottom: 10px;
}

.welcome-text {
    color: #475569;
    max-width: 680px;
    margin: auto;
    line-height: 1.7;
    font-size: 1rem;
}

.step-card {
    background: #FFFFFF;
    border: 1px solid #E2E8F0;
    border-radius: 14px;
    padding: 20px;
    min-height: 130px;
}

.step-title {
    font-size: 1.05rem;
    font-weight: 750;
    color: #0F172A;
    margin-bottom: 6px;
}

.step-text {
    color: #64748B;
    font-size: 0.9rem;
    line-height: 1.6;
}

/* ---------- NOTICES ---------- */

.notice {
    border-radius: 12px;
    padding: 12px 16px;
    margin: 10px 0;
    font-size: 0.92rem;
    line-height: 1.55;
    border: 1px solid;
}

.notice.info { background: #EFF6FF; border-color: #BFDBFE; color: #1E3A8A; }
.notice.warn { background: #FFFBEB; border-color: #FDE68A; color: #92400E; }
.notice.error { background: #FEF2F2; border-color: #FECACA; color: #991B1B; }
.notice.success { background: #F0FDF4; border-color: #BBF7D0; color: #166534; }

/* ---------- CASE BRIEF ---------- */

.chip-row {
    display: flex;
    flex-wrap: wrap;
    gap: 10px;
    margin-bottom: 14px;
}

.chip {
    background: #EFF6FF;
    border: 1px solid #DBEAFE;
    color: #1E3A8A;
    border-radius: 999px;
    padding: 6px 14px;
    font-size: 0.85rem;
}

.brief-grid {
    display: grid;
    grid-template-columns: repeat(2, minmax(0, 1fr));
    gap: 14px;
    margin-top: 6px;
}

@media (max-width: 900px) {
    .brief-grid { grid-template-columns: 1fr; }
}

.brief-card {
    background: #FFFFFF;
    border: 1px solid #E2E8F0;
    border-radius: 14px;
    padding: 16px 20px;
}

.brief-card.wide {
    grid-column: 1 / -1;
    border-left: 4px solid #2563EB;
}

.brief-label {
    font-size: 0.92rem;
    font-weight: 750;
    color: #2563EB;
    margin-bottom: 6px;
}

/* ---------- RICH TEXT (model output) ---------- */

.md {
    font-size: 0.95rem;
    line-height: 1.65;
    color: #1E293B;
}

.md p { margin: 0 0 0.6rem 0; }
.md ul { margin: 0.2rem 0 0.6rem 1.1rem; padding: 0; }
.md li { margin-bottom: 0.2rem; }

.md-h {
    font-weight: 750;
    color: #0F172A;
    margin: 0.9rem 0 0.3rem 0;
    display: flex;
    align-items: center;
    gap: 8px;
}

.md-num {
    display: inline-flex;
    width: 24px;
    height: 24px;
    border-radius: 50%;
    background: #DBEAFE;
    color: #1D4ED8;
    align-items: center;
    justify-content: center;
    font-size: 0.8rem;
    font-weight: 800;
    flex-shrink: 0;
}

.md-label {
    font-size: 0.85rem;
    font-weight: 750;
    color: #2563EB;
    margin: 0.7rem 0 0.1rem 0;
}

/* ---------- RESULT / FEEDBACK CARDS ---------- */

.result-card {
    background: #FFFFFF;
    border: 1px solid #E2E8F0;
    border-radius: 14px;
    padding: 20px 24px;
    margin: 8px 0 16px 0;
}

.result-head {
    display: flex;
    justify-content: space-between;
    align-items: center;
    gap: 12px;
    margin-bottom: 8px;
}

.result-title {
    font-size: 1.05rem;
    font-weight: 750;
    color: #0F172A;
}

.score-badge {
    border-radius: 999px;
    padding: 5px 15px;
    font-weight: 800;
    font-size: 0.9rem;
}

.score-badge.good { background: #DCFCE7; color: #166534; }
.score-badge.ok { background: #FEF3C7; color: #92400E; }
.score-badge.low { background: #FEE2E2; color: #991B1B; }

.fb-section {
    border-left: 3px solid #CBD5E1;
    padding: 2px 0 2px 14px;
    margin: 14px 0;
}

.fb-section.good { border-left-color: #16A34A; }
.fb-section.warn { border-left-color: #D97706; }
.fb-section.info { border-left-color: #2563EB; }

.fb-label {
    font-size: 0.85rem;
    font-weight: 750;
    color: #475569;
    margin-bottom: 2px;
}

/* ---------- QUESTION / SHOCK / BUBBLES ---------- */

.question-card {
    background: #FFFFFF;
    border: 1px solid #DBEAFE;
    border-left: 5px solid #2563EB;
    border-radius: 14px;
    padding: 22px 24px;
    margin: 10px 0 16px 0;
}

.question-label {
    color: #2563EB;
    font-size: 0.88rem;
    font-weight: 750;
    margin-bottom: 8px;
}

.question-text {
    color: #0F172A;
    font-size: 1.2rem;
    font-weight: 650;
    line-height: 1.55;
}

.shock-card {
    background: #FFF7ED;
    border: 1px solid #FED7AA;
    border-left: 5px solid #F97316;
    border-radius: 14px;
    padding: 22px 24px;
    margin: 10px 0 16px 0;
}

.shock-label {
    color: #C2410C;
    font-size: 0.88rem;
    font-weight: 750;
}

.shock-text {
    color: #0F172A;
    font-size: 1.15rem;
    font-weight: 650;
    line-height: 1.5;
    margin-top: 6px;
}

.shock-impact {
    color: #9A3412;
    margin-top: 10px;
    font-size: 0.95rem;
}

.bubble {
    border-radius: 12px;
    padding: 10px 14px;
    margin: 6px 0;
    font-size: 0.92rem;
    line-height: 1.6;
}

.bubble.coach { background: #EFF6FF; color: #1E3A8A; }
.bubble.you { background: #F1F5F9; color: #1E293B; margin-left: 28px; }

.bubble-who {
    font-size: 0.78rem;
    font-weight: 700;
    margin-bottom: 2px;
    opacity: 0.8;
}

/* ---------- PROFILE / TRUST ---------- */

.profile-label {
    font-size: 0.85rem;
    font-weight: 650;
    color: #64748B;
}

.profile-value {
    font-size: 1.25rem;
    font-weight: 750;
    color: #0F172A;
    margin-top: 6px;
}

.coach-insight {
    background: #EFF6FF;
    border: 1px solid #BFDBFE;
    border-left: 5px solid #2563EB;
    border-radius: 14px;
    padding: 16px 20px;
    color: #1E3A8A;
    line-height: 1.6;
}

.trust-list {
    margin: 6px 0 0 1.1rem;
    padding: 0;
    color: #1E293B;
    font-size: 0.92rem;
    line-height: 1.7;
}

/* ---------- DECISION MAP ---------- */

.dmap {
    background: #FFFFFF;
    border: 1px solid #E2E8F0;
    border-radius: 16px;
    padding: 28px 30px 32px 30px;
    margin: 6px 0 10px 0;
}

.dm-row {
    display: grid;
    gap: 28px;
}

.dm-row.single {
    grid-template-columns: minmax(0, 560px);
    justify-content: center;
}

.dm-row.pair {
    grid-template-columns: repeat(2, minmax(0, 1fr));
}

.dm-node {
    background: var(--bg);
    border: 1px solid #E2E8F0;
    border-top: 4px solid var(--c);
    border-radius: 14px;
    padding: 14px 18px 16px 18px;
    min-height: 84px;
    box-shadow: 0 1px 3px rgba(15, 23, 42, 0.06);
}

.dm-title {
    font-size: 0.95rem;
    font-weight: 750;
    color: var(--c);
    margin-bottom: 5px;
}

.dm-text {
    font-size: 0.88rem;
    line-height: 1.55;
    color: #334155;
    display: -webkit-box;
    -webkit-line-clamp: 4;
    -webkit-box-orient: vertical;
    overflow: hidden;
}

.dm-sub {
    font-size: 0.8rem;
    color: #94A3B8;
    margin-top: 4px;
}

.dm-case { --c: #0F172A; --bg: #0F172A; border-color: #0F172A; }
.dm-case .dm-title { color: #93C5FD; }
.dm-case .dm-text { color: #F8FAFC; font-weight: 600; font-size: 0.95rem; }
.dm-case .dm-sub { color: #94A3B8; }

.dm-problem { --c: #2563EB; --bg: #EFF6FF; }
.dm-causes { --c: #B45309; --bg: #FFFBEB; }
.dm-decision { --c: #6D28D9; --bg: #F5F3FF; }
.dm-options { --c: #15803D; --bg: #F0FDF4; }
.dm-tradeoffs { --c: #B91C1C; --bg: #FEF2F2; }

.dm-rec {
    --c: #475569;
    --bg: #FFFFFF;
    border: 2px dashed #94A3B8;
}

.dm-rec.filled {
    --c: #0F172A;
    border: 2px solid #0F172A;
}

/* connectors */

.dm-link { position: relative; height: 34px; }

.dm-link .av,
.dm-fork .stem,
.dm-fork .drop,
.dm-merge .stem,
.dm-merge .drop {
    position: absolute;
    width: 2px;
    margin-left: -1px;
    background: #A5B4C8;
}

.dm-link .av { left: 50%; top: 0; bottom: 0; }

.dm-fork, .dm-merge { position: relative; height: 46px; }

.dm-fork .dm-row,
.dm-merge .dm-row {
    position: absolute;
    top: 0; left: 0; right: 0; bottom: 0;
}

.fk { position: relative; }

.fk .bar {
    position: absolute;
    top: 23px;
    height: 2px;
    background: #A5B4C8;
}

.fk .bar.r { left: 50%; right: -14px; }
.fk .bar.l { left: -14px; right: 50%; }

.fk .drop { left: 50%; }

.dm-fork .stem { left: 50%; top: 0; height: 24px; }
.dm-fork .drop { top: 23px; bottom: 0; }

.dm-merge .drop { top: 0; height: 24px; }
.dm-merge .stem { left: 50%; top: 23px; bottom: 0; }

/* arrowheads */

.dm-link .av::after,
.dm-fork .drop::after,
.dm-merge .stem::after {
    content: "";
    position: absolute;
    left: 50%;
    bottom: -1px;
    transform: translateX(-50%);
    border-left: 6px solid transparent;
    border-right: 6px solid transparent;
    border-top: 8px solid #A5B4C8;
}

.dm-nlink { display: none; position: relative; height: 26px; }

@media (max-width: 800px) {
    .dm-row.pair { grid-template-columns: 1fr; gap: 14px; }
    .dm-fork, .dm-merge, .dm-row.pair.links { display: none; }
    .dm-nlink { display: block; }
    .dm-nlink .av {
        position: absolute; left: 50%; top: 0; bottom: 0;
        width: 2px; margin-left: -1px; background: #A5B4C8;
    }
    .dm-nlink .av::after {
        content: ""; position: absolute; left: 50%; bottom: -1px;
        transform: translateX(-50%);
        border-left: 6px solid transparent; border-right: 6px solid transparent;
        border-top: 8px solid #A5B4C8;
    }
    .dmap { padding: 20px 16px 24px 16px; }
}

/* ---------- STREAMLIT WIDGETS ---------- */

@MAIN button[kind="primary"],
@MAIN [data-testid="stBaseButton-primary"] {
    background-color: #2563EB !important;
    border: 1px solid #2563EB !important;
    border-radius: 10px !important;
}

@MAIN button[kind="primary"]:hover,
@MAIN [data-testid="stBaseButton-primary"]:hover {
    background-color: #1D4ED8 !important;
    border-color: #1D4ED8 !important;
}

@MAIN button[kind="primary"] p,
@MAIN [data-testid="stBaseButton-primary"] p {
    color: #FFFFFF !important;
    font-weight: 650;
}

@MAIN button[kind="secondary"],
@MAIN [data-testid="stBaseButton-secondary"] {
    background-color: #FFFFFF !important;
    border: 1px solid #CBD5E1 !important;
    border-radius: 10px !important;
}

@MAIN button[kind="secondary"]:hover,
@MAIN [data-testid="stBaseButton-secondary"]:hover {
    border-color: #2563EB !important;
}

@MAIN button[kind="secondary"] p,
@MAIN [data-testid="stBaseButton-secondary"] p {
    color: #1E293B !important;
    font-weight: 650;
}

@MAIN textarea,
@MAIN input[type="text"] {
    background-color: #FFFFFF !important;
    color: #0F172A !important;
    font-size: 0.97rem !important;
}

@MAIN [data-baseweb="textarea"],
@MAIN [data-baseweb="base-input"],
@MAIN [data-baseweb="input"] {
    background-color: #FFFFFF !important;
    border-color: #CBD5E1 !important;
    border-radius: 10px !important;
}

@MAIN [data-baseweb="textarea"]:focus-within,
@MAIN [data-baseweb="base-input"]:focus-within {
    border-color: #2563EB !important;
}

@MAIN textarea::placeholder,
@MAIN input::placeholder {
    color: #94A3B8 !important;
    opacity: 1;
}

@MAIN [data-baseweb="tab-list"] {
    gap: 6px;
}

@MAIN button[data-baseweb="tab"] {
    background: transparent;
    padding: 10px 16px;
}

@MAIN button[data-baseweb="tab"] p {
    color: #475569 !important;
    font-weight: 650;
}

@MAIN button[data-baseweb="tab"][aria-selected="true"] p {
    color: #2563EB !important;
}

@MAIN [data-baseweb="tab-highlight"] {
    background-color: #2563EB !important;
}

@MAIN [data-baseweb="tab-border"] {
    background-color: #E2E8F0 !important;
}

@MAIN [data-testid="stExpander"] {
    background-color: #FFFFFF;
    border: 1px solid #E2E8F0 !important;
    border-radius: 12px;
}

@MAIN [data-testid="stPlotlyChart"] {
    background-color: #FFFFFF;
    border: 1px solid #E2E8F0;
    border-radius: 14px;
    padding: 8px;
}

</style>
""".replace("@MAIN", MAIN)

st.markdown(CSS, unsafe_allow_html=True)


# ============================================================
# HTML / TEXT HELPERS
# ============================================================

def render_html(markup: str) -> None:
    """
    Render an HTML snippet safely.

    Streamlit runs st.markdown() text through a Markdown parser. Any line
    indented by 4+ spaces after a blank line becomes a code block, which is
    why cards were showing raw <div> tags. Flattening the snippet to one
    line removes both the indentation and the blank lines.
    """
    flat = " ".join(line.strip() for line in markup.splitlines() if line.strip())
    st.markdown(flat, unsafe_allow_html=True)


def esc(value) -> str:
    """HTML-escape any value so model output cannot break the layout."""
    return html.escape(str(value))


def plain_html(value) -> str:
    """Escape text but keep its line breaks."""
    return esc(value).replace("\r", "").replace("\n", "<br>")


def muted(text: str) -> None:
    render_html(f"<div class='muted'>{esc(text)}</div>")


def notice(kind: str, text: str) -> None:
    """kind: info | warn | error | success"""
    render_html(f"<div class='notice {kind}'>{esc(text)}</div>")


def section_heading(text: str) -> None:
    render_html(f"<div class='section-heading'>{esc(text)}</div>")


def kpi_card(label, value, sub, accent="") -> None:
    render_html(
        f"""
        <div class="kpi {accent}">
            <div class="kpi-label">{esc(label)}</div>
            <div class="kpi-value">{esc(value)}</div>
            <div class="kpi-sub">{esc(sub)}</div>
        </div>
        """
    )


def show_plotly(figure) -> None:
    """Display a Plotly figure on any Streamlit version, theme-independent."""
    for kwargs in (
        {"use_container_width": True, "theme": None},
        {"theme": None},
        {},
    ):
        try:
            st.plotly_chart(figure, **kwargs)
            return
        except TypeError:
            continue


def require_text(value, what: str) -> str:
    """Reject empty or non-text model output instead of showing garbage."""
    if value is None or not str(value).strip():
        raise ValueError(f"The AI returned an empty {what}. Please try again.")
    return str(value)


# ---------- light Markdown -> HTML (so every card is theme-proof) ----------

_BOLD = re.compile(r"\*\*(.+?)\*\*")
_BULLET = re.compile(r"^\s*[-*•]\s+(.*)$")
_NUMBERED = re.compile(r"^\s*(\d+)[.)]\s+(.*)$")
_HASH_HEAD = re.compile(r"^#{1,6}\s+(.*)$")
_LABEL_LINE = re.compile(r"^[A-Za-z][A-Za-z0-9 /&'’()\-]{1,58}:$")


def _inline(text: str) -> str:
    return _BOLD.sub(r"<b>\1</b>", html.escape(text))


def md_to_html(text) -> str:
    """Convert the small subset of Markdown the models produce into HTML."""
    out, paragraph, items = [], [], []

    def flush_paragraph():
        if paragraph:
            out.append("<p>" + " ".join(paragraph) + "</p>")
            paragraph.clear()

    def flush_items():
        if items:
            out.append("<ul>" + "".join(f"<li>{i}</li>" for i in items) + "</ul>")
            items.clear()

    for raw in str(text).splitlines():

        line = raw.strip()

        if not line:
            flush_paragraph()
            flush_items()
            continue

        head = _HASH_HEAD.match(line)
        if head:
            flush_paragraph()
            flush_items()
            out.append(f"<div class='md-h'>{_inline(head.group(1))}</div>")
            continue

        numbered = _NUMBERED.match(line)
        if numbered:
            flush_paragraph()
            flush_items()
            out.append(
                "<div class='md-h'>"
                f"<span class='md-num'>{numbered.group(1)}</span>"
                f"{_inline(numbered.group(2))}</div>"
            )
            continue

        bullet = _BULLET.match(line)
        if bullet:
            flush_paragraph()
            items.append(_inline(bullet.group(1)))
            continue

        bare = line.strip("*").strip()
        if _LABEL_LINE.match(bare):
            flush_paragraph()
            flush_items()
            out.append(f"<div class='md-label'>{_inline(bare.rstrip(':'))}</div>")
            continue

        flush_items()
        paragraph.append(_inline(line))

    flush_paragraph()
    flush_items()

    return "".join(out)


# ---------- "HEADING:" style section parsing ----------

SECTION_PATTERN = re.compile(
    r"^[ \t]*[#*]*[ \t]*([A-Z][A-Z0-9 /&'’()\-]{2,60}?)[ \t]*[*]*:[ \t]*[*]*[ \t]*$",
    re.MULTILINE,
)

SCORE_LINE = re.compile(
    r"^[ \t]*\**[ \t]*SCORE[ \t]*\**[ \t]*:?[ \t]*\**[ \t]*\d+(\.\d+)?[ \t]*/[ \t]*10[ \t]*\**[ \t]*$",
    re.IGNORECASE | re.MULTILINE,
)

HEADER_LABELS = {"Case Title", "Company / Organization", "Industry"}
WIDE_LABELS = {"Central Problem", "Key Decision To Be Made"}

SECTION_STYLE = {
    "strength": "good",
    "improvement": "warn",
    "missing": "warn",
    "challenge": "info",
    "key assumption": "info",
    "alternative view": "info",
    "follow-up question": "info",
}


def parse_sections(text: str, minimum: int = 3):
    """Split 'HEADING:' style model output into (label, body) pairs."""
    matches = list(SECTION_PATTERN.finditer(text))

    if len(matches) < minimum:
        return []

    sections = []

    for index, match in enumerate(matches):
        start = match.end()
        end = (
            matches[index + 1].start()
            if index + 1 < len(matches)
            else len(text)
        )
        body = text[start:end].strip()

        if body:
            sections.append((match.group(1).strip().title(), body))

    return sections


def score_class(score: float) -> str:
    if score >= 7:
        return "good"
    if score >= 5:
        return "ok"
    return "low"


def render_result(text, title: str, show_score: bool = False) -> None:
    """Render model feedback as a structured card with an optional score badge."""
    text = str(text)

    badge = ""

    if show_score:
        try:
            score = extract_score(text)
            score = float(score) if score is not None else None
        except Exception:
            score = None

        if score is not None:
            badge = (
                f"<span class='score-badge {score_class(score)}'>"
                f"{score:g}/10</span>"
            )

    cleaned = SCORE_LINE.sub("", text)

    sections = [
        s for s in parse_sections(cleaned, minimum=2)
        if s[0].lower() != "score"
    ]

    if sections:
        body = ""
        for label, content in sections:
            style = SECTION_STYLE.get(label.lower(), "")
            body += (
                f"<div class='fb-section {style}'>"
                f"<div class='fb-label'>{esc(label)}</div>"
                f"<div class='md'>{md_to_html(content)}</div>"
                "</div>"
            )
    else:
        body = f"<div class='md'>{md_to_html(cleaned)}</div>"

    render_html(
        "<div class='result-card'>"
        "<div class='result-head'>"
        f"<div class='result-title'>{esc(title)}</div>{badge}"
        "</div>"
        f"{body}"
        "</div>"
    )


def render_case_brief(text: str) -> None:

    sections = parse_sections(text, minimum=3)

    # If the model used an unexpected format, fall back to one card.
    if not sections:
        render_html(
            "<div class='result-card'>"
            f"<div class='md'>{md_to_html(text)}</div>"
            "</div>"
        )
        return

    header = [s for s in sections if s[0] in HEADER_LABELS]
    body = [s for s in sections if s[0] not in HEADER_LABELS]

    if header:
        chips = "".join(
            f"<span class='chip'><b>{esc(label)}:</b> "
            f"{esc(' '.join(content.split()))}</span>"
            for label, content in header
        )
        render_html(f"<div class='chip-row'>{chips}</div>")

    cards = ""

    for label, content in body:
        wide = " wide" if label in WIDE_LABELS else ""
        cards += (
            f"<div class='brief-card{wide}'>"
            f"<div class='brief-label'>{esc(label)}</div>"
            f"<div class='md'>{md_to_html(content)}</div>"
            "</div>"
        )

    render_html(f"<div class='brief-grid'>{cards}</div>")


# ============================================================
# DECISION MAP (HTML/CSS, built from the case analysis)
# ============================================================

def short_text(text, limit: int = 150) -> str:
    """One-line preview of a section, cut at a word boundary."""
    flat = " ".join(str(text).replace("*", "").split())

    if len(flat) <= limit:
        return flat

    return flat[:limit].rsplit(" ", 1)[0].rstrip(",;:.") + "…"


def map_node(css: str, title: str, text: str, sub: str = "") -> str:
    tip = esc(" ".join(str(text).split()))
    sub_html = f"<div class='dm-sub'>{esc(sub)}</div>" if sub else ""

    return (
        f"<div class='dm-node {css}' title='{tip}'>"
        f"<div class='dm-title'>{esc(title)}</div>"
        f"<div class='dm-text'>{esc(short_text(text))}</div>"
        f"{sub_html}</div>"
    )


_ARROW = "<div class='dm-nlink'><div class='av'></div></div>"


def decision_map_html(analysis: str, recommendation: str = "") -> str:
    """
    Build the decision map from the structured case analysis.
    Returns "" if the analysis does not contain enough sections.
    """
    sections = parse_sections(analysis, minimum=3)

    def pick(*keys):
        for label, body in sections:
            if any(key in label.lower() for key in keys):
                return body
        return ""

    problem = pick("central problem")
    causes = pick("root cause")
    decision = pick("key decision")
    options = pick("strategic option")
    tradeoffs = pick("trade")

    found = sum(bool(x) for x in (problem, causes, decision, options, tradeoffs))

    if found < 3:
        return ""

    missing = "Not identified in the case analysis."

    case_title = short_text(pick("case title") or "The case", 90)
    company = short_text(pick("company"), 40)
    industry = short_text(pick("industry"), 40)
    sub = f"{company} ({industry})" if company and industry else (company or industry)

    if recommendation.strip():
        rec_node = map_node(
            "dm-rec filled",
            "Your recommendation",
            recommendation,
        )
    else:
        rec_node = map_node(
            "dm-rec",
            "Your recommendation",
            "Pick an option, back it with evidence from the case, then "
            "test it in Devil's Advocate and Stress Test.",
        )

    fork = (
        "<div class='dm-fork'><div class='stem'></div>"
        "<div class='dm-row pair'>"
        "<div class='fk'><div class='bar r'></div><div class='drop'></div></div>"
        "<div class='fk'><div class='bar l'></div><div class='drop'></div></div>"
        "</div></div>"
    )

    merge = (
        "<div class='dm-merge'><div class='stem'></div>"
        "<div class='dm-row pair'>"
        "<div class='fk'><div class='bar r'></div><div class='drop'></div></div>"
        "<div class='fk'><div class='bar l'></div><div class='drop'></div></div>"
        "</div></div>"
    )

    straight = (
        "<div class='dm-row pair links'>"
        "<div class='dm-link'><div class='av'></div></div>"
        "<div class='dm-link'><div class='av'></div></div>"
        "</div>"
    )

    single_link = "<div class='dm-link'><div class='av'></div></div>"

    return (
        "<div class='dmap'>"
        f"<div class='dm-row single'>{map_node('dm-case', 'The case', case_title, sub)}</div>"
        f"{single_link}"
        f"<div class='dm-row single'>{map_node('dm-problem', 'Central problem', problem or missing)}</div>"
        f"{fork}{_ARROW}"
        "<div class='dm-row pair'>"
        f"{map_node('dm-causes', 'Root causes', causes or missing)}"
        f"{map_node('dm-decision', 'Key decision', decision or missing)}"
        "</div>"
        f"{straight}{_ARROW}"
        "<div class='dm-row pair'>"
        f"{map_node('dm-options', 'Strategic options', options or missing)}"
        f"{map_node('dm-tradeoffs', 'Key trade-offs', tradeoffs or missing)}"
        "</div>"
        f"{merge}{_ARROW}"
        f"<div class='dm-row single'>{rec_node}</div>"
        "</div>"
    )


# ============================================================
# INPUT VALIDATION & GUARDRAILS
# ============================================================

MIN_WORDS = 12
MAX_CHARS = 8000

INJECTION_PATTERN = re.compile(
    r"(ignore\s+(all\s+|any\s+|the\s+|your\s+)?(previous|prior|above|earlier)\s+"
    r"(instructions?|prompts?|rules)"
    r"|disregard\s+(all\s+|your\s+|the\s+)?(instructions?|rules|prompt)"
    r"|(reveal|show|print)\s+(me\s+)?(your|the)\s+(system\s+)?prompt"
    r"|you\s+are\s+now\s+(a|an|in)\b"
    r"|developer\s+mode"
    r"|jailbreak)",
    re.IGNORECASE,
)


def validate_text(text: str, label: str = "answer"):
    """Return an error message if the input should not reach the model."""
    cleaned = text.strip()

    if not cleaned:
        return f"Please write your {label} first."

    if INJECTION_PATTERN.search(cleaned):
        return (
            "This looks like an attempt to change the coach's instructions. "
            "CaseCraft only evaluates your reasoning about the case, so "
            f"please rewrite your {label} as case analysis."
        )

    words = len(cleaned.split())

    if words < MIN_WORDS:
        return (
            f"Your {label} is only {words} words. Explain your reasoning and "
            f"cite at least one fact from the case (aim for {MIN_WORDS}+ words)."
        )

    if len(cleaned) > MAX_CHARS:
        return (
            f"Your {label} is too long ({len(cleaned):,} characters). "
            f"Please keep it under {MAX_CHARS:,}."
        )

    return None


# ============================================================
# SAMPLE CASE (fictional, written for demos)
# ============================================================

SAMPLE_CASE_NAME = "Sample case: Chai Junction (fictional)"

SAMPLE_CASE_TEXT = """
Chai Junction: Choosing the Next Phase of Growth (fictional teaching case)

Chai Junction is a regional tea-cafe chain with 42 company-owned outlets across three
Indian cities. In FY25 it earned revenue of Rs 180 crore at an EBITDA margin of 11%.
Same-store sales growth has slowed from 14% to 5% in two years. Rent and staff costs
have risen about 9% a year, while the average bill has stayed flat at Rs 165.

Two national coffee chains are opening outlets in Chai Junction's cities, and
quick-commerce brands now sell ready-to-drink tea. A customer survey found that 38% of
orders at the metro outlets already come through delivery apps. In the same survey,
71% of customers rated quality as "excellent" at company-owned outlets, compared with
54% at three pilot franchise outlets.

Founder and CEO Meera Iyer has Rs 60 crore of capital available and three options
before a board meeting in two weeks.

Option A - Franchise expansion. Open 60 franchised outlets in tier-2 cities over three
years. Franchisees fund their own outlets. Chai Junction invests Rs 0.4 crore per outlet
in training and supply chain and earns a 7% royalty on sales. Quality control is a risk.

Option B - Delivery-only kitchens. Build 25 cloud kitchens at Rs 0.5 crore each. Delivery
platforms charge a 22-25% commission on every order.

Option C - Packaged tea retail. Invest Rs 35 crore in a manufacturing line to sell packaged
tea through modern trade and quick-commerce. Gross margin would be 38% compared with 62%
in the cafes, and the payback period is uncertain.

The CFO warns that the company's loan covenant requires net debt to stay below 2.5 times
EBITDA. It is currently 1.4 times. The board is divided, and no option has majority support.
"""


# ============================================================
# SESSION STATE
# ============================================================

GLOBAL_DEFAULTS = {
    "case_text": "",
    "case_name": "",
    "case_loaded": False,
    "case_version": 0,
    "demo_mode": False,
}

CASE_DEFAULTS = {
    "case_analysis": "",
    "analysis_done": False,

    "question": "",
    "question_count": 0,
    "conversation": [],
    "answer_evaluations": [],

    "framework_recommendation": "",
    "framework_evaluation": "",

    "devils_advocate": "",

    "stress_scenario": None,
    "stress_evaluation": "",
    "stress_round": 0,

    "scores": [],
    "score_log": [],
}

for _key, _value in {**GLOBAL_DEFAULTS, **CASE_DEFAULTS}.items():
    if _key not in st.session_state:
        st.session_state[_key] = copy.deepcopy(_value)


def reset_case_state() -> None:
    """Clear all progress for the current case."""
    for key, value in CASE_DEFAULTS.items():
        st.session_state[key] = copy.deepcopy(value)
    st.session_state.case_version += 1


def load_case(name: str, text: str) -> None:
    """Load a new case and start from a clean slate."""
    reset_case_state()
    st.session_state.case_text = text
    st.session_state.case_name = name
    st.session_state.case_loaded = True


def record_score(module: str, score) -> None:
    """Store a score for the overall average and for the module charts."""
    if score is None:
        return
    try:
        value = float(score)
    except (TypeError, ValueError):
        return
    st.session_state.scores.append(score)
    st.session_state.score_log.append({"module": module, "score": value})


# ============================================================
# DEMO CONTENT
# ============================================================

def demo_analysis():

    return """
CASE TITLE:
Strategic Growth Decision

COMPANY / ORGANIZATION:
Case Company

INDUSTRY:
Consumer Business

CENTRAL PROBLEM:
The company must decide how to pursue future growth while managing
competitive pressure, investment requirements and execution risk.

KEY DECISION TO BE MADE:
Management must determine which strategic option offers the strongest
balance between growth, profitability and risk.

IMPORTANT FACTS:
The company operates in a competitive environment and has limited
resources available for strategic expansion.

KEY STAKEHOLDERS:
Senior management, employees, customers, competitors and investors.

POSSIBLE ROOT CAUSES:
Competitive pressure, changing customer preferences, resource
constraints and uncertainty regarding future market conditions.

RELEVANT BUSINESS FRAMEWORKS:
SWOT Analysis, Porter's Five Forces, Scenario Analysis.

IMPORTANT DATA / NUMBERS:
Use the quantitative evidence contained in the case.

KEY TRADE-OFFS:
Growth versus risk, investment versus return, and short-term
performance versus long-term strategic positioning.

INFORMATION THAT IS MISSING:
More information may be required about implementation costs,
competitor reactions and expected financial returns.

POTENTIAL STRATEGIC OPTIONS:
Management can compare multiple strategic alternatives using
financial, competitive and operational criteria.
"""


def demo_question():

    return (
        "What is the single most important problem management needs "
        "to solve, and what evidence from the case supports your view?"
    )


def demo_evaluation():

    return """
STRENGTH:
Your response identifies the central issue and attempts to support
your reasoning with case evidence.

IMPROVEMENT:
Make the causal connection between your evidence and conclusion
more explicit.

SCORE:
7/10
"""


def demo_framework():

    return """
1. SWOT Analysis

Why it is relevant:
Helps distinguish internal capabilities from external opportunities
and threats.

What to investigate:
Strengths, weaknesses, opportunities and threats.

2. Porter's Five Forces

Why it is relevant:
Helps evaluate competitive pressure within the industry.

What to investigate:
Rivalry, buyers, suppliers, substitutes and new entrants.

3. Scenario Analysis

Why it is relevant:
Helps evaluate strategic choices under uncertainty.

What to investigate:
Alternative market, competitive and demand scenarios.

RECOMMENDED FRAMEWORK:
SWOT Analysis
"""


def demo_framework_eval():

    return """
STRENGTH:
You selected a framework that is relevant to the strategic problem.

MISSING:
Your analysis should connect each framework factor to specific
evidence from the case.

CHALLENGE:
Which finding would most strongly change your strategic decision?

SCORE:
7/10
"""


def demo_challenge():

    return """
KEY ASSUMPTION:
The recommendation assumes that market conditions will remain
relatively stable.

CHALLENGE:
What happens if the main competitor responds aggressively?

ALTERNATIVE VIEW:
A less aggressive strategy may reduce risk while preserving
financial flexibility.

FOLLOW-UP QUESTION:
What evidence would convince you that your recommendation is
superior to the alternative?
"""


def demo_stress_scenario():

    return {
        "scenario": (
            "A major competitor announces a price cut of 15% across "
            "all of its products with immediate effect."
        ),
        "impact": (
            "Customers become more price-sensitive and your expected "
            "margins and market share are put under pressure."
        ),
    }


def demo_stress_evaluation():

    return """
STRENGTH:
You recognized how the business shock changes the feasibility
of the original recommendation.

IMPROVEMENT:
Quantify the impact where possible and explain which strategic
trade-off becomes more important.

SCORE:
7/10
"""


def valid_scenario(scenario) -> bool:
    return (
        isinstance(scenario, dict)
        and str(scenario.get("scenario", "")).strip() != ""
        and str(scenario.get("impact", "")).strip() != ""
    )


# ============================================================
# CHARTS
# ============================================================

CHART_LAYOUT = dict(
    paper_bgcolor="#FFFFFF",
    plot_bgcolor="#FFFFFF",
    font=dict(color="#334155", family="Plus Jakarta Sans, Segoe UI, sans-serif"),
    margin=dict(l=44, r=24, t=24, b=44),
    height=300,
    showlegend=False,
)


def build_trend_figure(log):

    xs = list(range(1, len(log) + 1))
    ys = [entry["score"] for entry in log]
    modules = [entry["module"] for entry in log]

    figure = go.Figure(
        go.Scatter(
            x=xs,
            y=ys,
            mode="lines+markers",
            line=dict(color="#2563EB", width=3),
            marker=dict(size=10, color="#2563EB"),
            customdata=modules,
            hovertemplate="Attempt %{x} (%{customdata})<br>Score %{y}/10<extra></extra>",
        )
    )

    figure.add_shape(
        type="line",
        x0=0.5,
        x1=len(xs) + 0.5,
        y0=7,
        y1=7,
        line=dict(color="#16A34A", width=1.5, dash="dot"),
    )

    figure.add_annotation(
        x=len(xs) + 0.5,
        y=7,
        text="Target: 7",
        showarrow=False,
        xanchor="right",
        yanchor="bottom",
        font=dict(color="#16A34A", size=11),
    )

    figure.update_layout(**CHART_LAYOUT)
    figure.update_xaxes(
        title="Attempt",
        dtick=1,
        range=[0.5, len(xs) + 0.5],
        gridcolor="#EEF2F7",
    )
    figure.update_yaxes(title="Score", range=[0, 10], gridcolor="#EEF2F7")

    return figure


def build_module_figure(log):

    totals = {}

    for entry in log:
        totals.setdefault(entry["module"], []).append(entry["score"])

    modules = list(totals.keys())
    averages = [round(sum(v) / len(v), 1) for v in totals.values()]

    figure = go.Figure(
        go.Bar(
            x=modules,
            y=averages,
            marker_color="#2563EB",
            text=averages,
            textposition="outside",
            hovertemplate="%{x}<br>Average %{y}/10<extra></extra>",
        )
    )

    figure.update_layout(**CHART_LAYOUT)
    figure.update_yaxes(title="Average score", range=[0, 10.5], gridcolor="#EEF2F7")

    return figure


# ============================================================
# SIDEBAR
# ============================================================

with st.sidebar:

    render_html("<div class='side-brand'>CaseCraft AI</div>")
    render_html("<div class='side-tagline'>MBA Case Reasoning Simulator</div>")

    st.markdown("---")

    render_html("<div class='side-section'>Upload case study</div>")

    uploaded_file = st.file_uploader(
        "Upload PDF or TXT",
        type=["pdf", "txt"],
        label_visibility="collapsed",
    )

    st.markdown("---")

    st.toggle("Demo / Offline Mode", key="demo_mode")

    if st.session_state.demo_mode:
        render_html("<div class='side-note'>Demo mode makes no AI calls.</div>")
    else:
        render_html(
            "<div class='side-note'>Live mode uses the AI service.</div>"
        )

    st.markdown("---")

    render_html(
        """
        <div class="side-note">
        <b>Privacy:</b> in Live mode, case text and your answers are sent to a
        third-party AI provider. Do not upload confidential material.<br><br>
        <b>Accuracy:</b> AI feedback and scores are coaching aids and can be
        wrong. They are not grades.
        </div>
        """
    )

    st.markdown("---")

    render_html(
        """
        <div class="side-note">
        <b>Think</b> the case.<br>
        <b>Defend</b> the decision.<br>
        <b>Improve</b> your reasoning.
        </div>
        """
    )


# ============================================================
# LOAD UPLOADED CASE
# ============================================================

upload_error = None

if uploaded_file is not None and st.session_state.case_name != uploaded_file.name:

    try:
        extracted = extract_case_text(uploaded_file)

        if not extracted or not str(extracted).strip():
            raise ValueError(
                "No readable text was found. Scanned PDFs need OCR; "
                "try a text-based PDF or a TXT file."
            )

    except Exception as error:

        upload_error = f"Could not read this file: {error}"

    else:

        load_case(uploaded_file.name, str(extracted))


# ============================================================
# APP BAR
# ============================================================

if st.session_state.demo_mode:
    mode_pill = "<span class='pill demo'>● Demo mode</span>"
else:
    mode_pill = "<span class='pill live'>● Live AI</span>"

case_pill = (
    f"<span class='pill case'>{esc(st.session_state.case_name)}</span>"
    if st.session_state.case_loaded
    else ""
)

render_html(
    f"""
    <div class="appbar">
        <div class="appbar-left">
            <div class="logo">◆</div>
            <div>
                <div class="appbar-title">CaseCraft AI</div>
                <div class="appbar-sub">Think the case. Defend the decision.</div>
            </div>
        </div>
        <div class="appbar-right">{case_pill}{mode_pill}</div>
    </div>
    """
)

if upload_error:
    notice("error", upload_error)


# ============================================================
# NO CASE LOADED
# ============================================================

if not st.session_state.case_loaded:

    render_html(
        """
        <div class="welcome-card">
            <div class="welcome-title">Start a case</div>
            <div class="welcome-text">
                Upload an MBA business case from the sidebar, or try the
                built-in sample. CaseCraft AI turns the case into a structured
                decision problem and coaches you through analysis, frameworks,
                strategic decisions and stress-testing.
            </div>
        </div>
        """
    )

    step_columns = st.columns(3)

    steps = [
        (
            "Think",
            "Answer Socratic questions. The coach asks; it does not hand "
            "you the answer.",
        ),
        (
            "Defend",
            "Pick frameworks, state a recommendation and have its "
            "assumptions challenged.",
        ),
        (
            "Stress-test",
            "See whether your strategy survives a sudden business shock.",
        ),
    ]

    for column, (title, text) in zip(step_columns, steps):
        with column:
            render_html(
                f"""
                <div class="step-card">
                    <div class="step-title">{esc(title)}</div>
                    <div class="step-text">{esc(text)}</div>
                </div>
                """
            )

    st.markdown("")

    if st.button("Try the sample case", type="primary"):
        load_case(SAMPLE_CASE_NAME, SAMPLE_CASE_TEXT)
        st.rerun()

    muted(
        "The sample is a short fictional case, so you can explore every "
        "feature without uploading anything."
    )

    st.stop()


# ============================================================
# CASE HEADER + PROGRESS
# ============================================================

version = st.session_state.case_version

word_count = len(st.session_state.case_text.split())

header_left, header_right = st.columns([6, 1])

with header_left:

    render_html(
        f"""
        <div class="card">
            <div class="case-name-label">Active case</div>
            <div class="case-name">{esc(st.session_state.case_name)}</div>
            <div class="case-meta">{word_count:,} words</div>
        </div>
        """
    )

with header_right:

    if st.button("Restart case", help="Clear all progress for this case"):
        reset_case_state()
        st.rerun()


def render_stepper():

    state = st.session_state

    steps = [
        ("Analyze case", state.analysis_done),
        ("Think", state.question_count > 0),
        ("Frameworks", bool(state.framework_evaluation)),
        ("Challenge", bool(state.devils_advocate)),
        ("Stress test", bool(state.stress_evaluation)),
    ]

    first_pending = next(
        (i for i, (_, done) in enumerate(steps) if not done), None
    )

    parts = []

    for index, (name, done) in enumerate(steps):

        if done:
            css = "done"
        elif index == first_pending:
            css = "current"
        else:
            css = ""

        dot = "✓" if done else str(index + 1)

        parts.append(
            f"<div class='step {css}'><span class='dot'>{dot}</span>"
            f"<span class='step-name'>{esc(name)}</span></div>"
        )

        if index < len(steps) - 1:
            line_css = "done" if done else ""
            parts.append(f"<div class='step-line {line_css}'></div>")

    render_html("<div class='stepper'>" + "".join(parts) + "</div>")

    return sum(1 for _, done in steps if done), len(steps)


completed_steps, total_steps = render_stepper()


# ============================================================
# CASE ANALYSIS
# ============================================================

if not st.session_state.analysis_done:

    section_heading("Prepare your case")

    notice(
        "info",
        "The first step is to convert the case into a structured "
        "decision problem.",
    )

    if st.button("Analyze Case", type="primary"):

        with st.spinner("Analyzing case..."):

            try:

                if st.session_state.demo_mode:
                    result = demo_analysis()
                else:
                    result = analyze_case(st.session_state.case_text)

                result = require_text(result, "case analysis")

            except Exception as error:

                notice("error", f"Case analysis failed: {error}")
                muted(
                    "You can retry, or switch on Demo / Offline Mode in "
                    "the sidebar to continue without the AI service."
                )

            else:

                st.session_state.case_analysis = result
                st.session_state.analysis_done = True
                st.rerun()

    st.stop()


# ============================================================
# DASHBOARD METRICS
# ============================================================

scores = st.session_state.scores

overall_score = calculate_score(scores)

performance = performance_label(overall_score)

metrics = st.columns(4)

with metrics[0]:
    kpi_card(
        "Progress",
        f"{completed_steps}/{total_steps}",
        "Modules completed",
    )

with metrics[1]:
    kpi_card(
        "Answers",
        st.session_state.question_count,
        "Coaching questions answered",
        "violet",
    )

with metrics[2]:
    kpi_card(
        "Reasoning score",
        f"{overall_score:.1f}/10",
        "Average across evaluations",
        "green",
    )

with metrics[3]:
    kpi_card(
        "Performance",
        performance,
        "Current level",
        "amber",
    )

st.markdown("")


# ============================================================
# NAVIGATION TABS
# ============================================================

tabs = st.tabs(
    [
        "📋 Case Brief",
        "🧠 Think",
        "📊 Framework Lab",
        "⚔️ Devil's Advocate",
        "🔥 Stress Test",
        "🏆 Scorecard",
    ]
)


# ============================================================
# CASE BRIEF
# ============================================================

with tabs[0]:

    section_heading("Case brief")

    muted(
        "Structured analysis of the case. CaseCraft AI does not provide "
        "the final recommendation at this stage."
    )

    render_case_brief(st.session_state.case_analysis)

    section_heading("Decision map")

    map_markup = decision_map_html(
        st.session_state.case_analysis,
        st.session_state.get(f"recommendation_input_{version}", ""),
    )

    if map_markup:

        render_html(map_markup)

        muted(
            "Cards are built from your case analysis. The dashed card at "
            "the bottom fills in with your own recommendation once you "
            "write one in the Devil's Advocate tab."
        )

    else:

        # Fall back to the original Plotly map if the analysis has an
        # unexpected format.
        try:

            figure = create_case_map(st.session_state.case_analysis)

            try:
                figure.update_layout(
                    paper_bgcolor="#FFFFFF",
                    font=dict(color="#1E293B"),
                )
            except Exception:
                pass

            show_plotly(figure)

        except Exception as error:

            notice(
                "info",
                f"Decision map is unavailable for this case ({error}).",
            )


# ============================================================
# THINK
# ============================================================

with tabs[1]:

    section_heading("Think")

    muted(
        "Develop your reasoning through Socratic questioning instead "
        "of receiving the answer directly."
    )

    if not st.session_state.question:

        if st.button("Start Coaching", type="primary"):

            with st.spinner("Preparing your first coaching question..."):

                try:

                    if st.session_state.demo_mode:
                        question = demo_question()
                    else:
                        question = generate_coaching_question(
                            st.session_state.case_text,
                            st.session_state.case_analysis,
                            st.session_state.conversation,
                        )

                    question = require_text(question, "question")

                except Exception as error:

                    notice("error", f"Could not generate a question: {error}")

                else:

                    st.session_state.question = question
                    st.rerun()

    else:

        render_html(
            f"""
            <div class="question-card">
                <div class="question-label">
                    Coaching question {st.session_state.question_count + 1}
                </div>
                <div class="question-text">
                    {plain_html(st.session_state.question)}
                </div>
            </div>
            """
        )

        answer = st.text_area(
            "Your answer",
            height=180,
            placeholder="Build your reasoning using evidence from the case...",
            key=f"think_answer_{version}_{st.session_state.question_count}",
        )

        if st.button("Submit Answer", type="primary"):

            problem = validate_text(answer, "answer")

            if problem:

                notice("warn", problem)

            else:

                with st.spinner("Evaluating your reasoning..."):

                    try:

                        current_question = st.session_state.question

                        if st.session_state.demo_mode:
                            evaluation = demo_evaluation()
                        else:
                            evaluation = evaluate_student_answer(
                                st.session_state.case_text,
                                current_question,
                                answer,
                            )

                        evaluation = require_text(evaluation, "evaluation")

                        score = extract_score(evaluation)

                        updated_conversation = (
                            st.session_state.conversation
                            + [(current_question, answer)]
                        )

                        if st.session_state.demo_mode:
                            next_question = demo_question()
                        else:
                            next_question = generate_coaching_question(
                                st.session_state.case_text,
                                st.session_state.case_analysis,
                                updated_conversation,
                            )

                        next_question = require_text(
                            next_question, "next question"
                        )

                    except Exception as error:

                        notice("error", f"Evaluation failed: {error}")
                        muted(
                            "Your answer is still in the box. Try again, "
                            "or switch to Demo / Offline Mode."
                        )

                    else:

                        # Only update state once every step has succeeded.
                        st.session_state.conversation = updated_conversation
                        st.session_state.answer_evaluations.append(evaluation)
                        record_score("Think", score)

                        st.session_state.question_count += 1
                        st.session_state.question = next_question

                        st.rerun()

    evaluations = st.session_state.answer_evaluations

    if evaluations:

        section_heading("Latest feedback")

        render_result(
            evaluations[-1],
            f"Feedback on question {len(evaluations)}",
            show_score=True,
        )

        if len(evaluations) > 1:

            with st.expander("Previous questions and feedback"):

                conversation = st.session_state.conversation

                for index in range(len(evaluations) - 2, -1, -1):

                    if index < len(conversation):

                        asked, replied = conversation[index]

                        render_html(
                            f"""
                            <div class="bubble coach">
                                <div class="bubble-who">Coach</div>
                                {plain_html(asked)}
                            </div>
                            <div class="bubble you">
                                <div class="bubble-who">You</div>
                                {plain_html(replied)}
                            </div>
                            """
                        )

                    render_result(
                        evaluations[index],
                        f"Feedback on question {index + 1}",
                        show_score=True,
                    )


# ============================================================
# FRAMEWORK LAB
# ============================================================

with tabs[2]:

    section_heading("Framework lab")

    muted(
        "Select analytical frameworks based on the problem rather "
        "than using frameworks mechanically."
    )

    if st.button("Recommend Frameworks", type="primary"):

        with st.spinner("Selecting the most relevant frameworks..."):

            try:

                if st.session_state.demo_mode:
                    result = demo_framework()
                else:
                    result = recommend_framework(st.session_state.case_text)

                result = require_text(result, "framework recommendation")

            except Exception as error:

                notice("error", f"Framework recommendation failed: {error}")

            else:

                st.session_state.framework_recommendation = result
                st.rerun()

    if st.session_state.framework_recommendation:

        render_result(
            st.session_state.framework_recommendation,
            "Recommended frameworks",
        )

        section_heading("Apply a framework")

        framework_name = st.text_input(
            "Framework name",
            placeholder="Example: SWOT Analysis",
            key=f"framework_name_{version}",
        )

        framework_analysis = st.text_area(
            "Your analysis",
            height=180,
            placeholder="Apply the framework using evidence from the case...",
            key=f"framework_analysis_{version}",
        )

        if st.button("Evaluate Framework Analysis", type="primary"):

            if not framework_name.strip():

                notice("warn", "Enter the name of the framework you used.")

            elif len(framework_name.strip()) > 80:

                notice("warn", "The framework name is too long (80 characters max).")

            else:

                problem = validate_text(framework_analysis, "analysis")

                if problem:

                    notice("warn", problem)

                else:

                    with st.spinner("Evaluating your framework analysis..."):

                        try:

                            if st.session_state.demo_mode:
                                result = demo_framework_eval()
                            else:
                                result = evaluate_framework(
                                    st.session_state.case_text,
                                    framework_name,
                                    framework_analysis,
                                )

                            result = require_text(result, "evaluation")

                            score = extract_score(result)

                        except Exception as error:

                            notice("error", f"Evaluation failed: {error}")

                        else:

                            st.session_state.framework_evaluation = result
                            record_score("Framework", score)
                            st.rerun()

    if st.session_state.framework_evaluation:

        section_heading("Framework feedback")

        render_result(
            st.session_state.framework_evaluation,
            "Framework evaluation",
            show_score=True,
        )


# ============================================================
# DEVIL'S ADVOCATE
# ============================================================

with tabs[3]:

    section_heading("Devil's advocate")

    muted(
        "Give your recommendation. CaseCraft AI will challenge "
        "the assumptions behind it."
    )

    recommendation = st.text_area(
        "Your recommendation",
        height=180,
        placeholder="State your recommendation and explain why you chose it...",
        key=f"recommendation_input_{version}",
    )

    if st.button("Challenge My Recommendation", type="primary"):

        problem = validate_text(recommendation, "recommendation")

        if problem:

            notice("warn", problem)

        else:

            with st.spinner("Challenging your recommendation..."):

                try:

                    if st.session_state.demo_mode:
                        result = demo_challenge()
                    else:
                        result = generate_challenge(
                            st.session_state.case_text,
                            recommendation,
                        )

                    result = require_text(result, "challenge")

                except Exception as error:

                    notice("error", f"Challenge generation failed: {error}")

                else:

                    st.session_state.devils_advocate = result
                    st.rerun()

    if st.session_state.devils_advocate:

        section_heading("The challenge")

        render_result(
            st.session_state.devils_advocate,
            "Devil's advocate response",
        )


# ============================================================
# STRESS TEST
# ============================================================

with tabs[4]:

    section_heading("Stress test")

    muted(
        "Test whether your recommendation survives a change in "
        "business conditions."
    )

    if st.button("Generate Business Shock", type="primary"):

        try:

            if st.session_state.demo_mode:
                new_scenario = demo_stress_scenario()
            else:
                new_scenario = generate_stress_test()

            if not valid_scenario(new_scenario):
                raise ValueError(
                    "The AI returned an incomplete scenario. "
                    "Please generate another."
                )

        except Exception as error:

            notice("error", f"Could not generate a stress test: {error}")

        else:

            st.session_state.stress_scenario = new_scenario
            st.session_state.stress_evaluation = ""
            st.session_state.stress_round += 1
            st.rerun()

    if st.session_state.stress_scenario:

        scenario = st.session_state.stress_scenario

        render_html(
            f"""
            <div class="shock-card">
                <div class="shock-label">Business shock</div>
                <div class="shock-text">{plain_html(scenario["scenario"])}</div>
                <div class="shock-impact">
                    <b>Potential impact:</b> {plain_html(scenario["impact"])}
                </div>
            </div>
            """
        )

        stress_response = st.text_area(
            "How would you adapt your strategy?",
            height=180,
            placeholder=(
                "Explain how the business shock changes your recommendation..."
            ),
            key=f"stress_response_{version}_{st.session_state.stress_round}",
        )

        if st.button("Evaluate Stress Response", type="primary"):

            problem = validate_text(stress_response, "response")

            if problem:

                notice("warn", problem)

            else:

                with st.spinner("Evaluating your response..."):

                    try:

                        if st.session_state.demo_mode:
                            result = demo_stress_evaluation()
                        else:
                            result = evaluate_stress_test(
                                st.session_state.case_text,
                                scenario["scenario"],
                                stress_response,
                            )

                        result = require_text(result, "evaluation")

                        score = extract_score(result)

                    except Exception as error:

                        notice("error", f"Stress-test evaluation failed: {error}")

                    else:

                        st.session_state.stress_evaluation = result
                        record_score("Stress test", score)
                        st.rerun()

    if st.session_state.stress_evaluation:

        section_heading("Stress-test feedback")

        render_result(
            st.session_state.stress_evaluation,
            "Stress-test evaluation",
            show_score=True,
        )


# ============================================================
# SCORECARD
# ============================================================

with tabs[5]:

    section_heading("Performance scorecard")

    muted(
        "Scores are produced by an AI model and are indicative only. "
        "The same answer can receive slightly different scores on "
        "different runs."
    )

    scores = st.session_state.scores
    score_log = st.session_state.score_log

    overall_score = calculate_score(scores)

    performance = performance_label(overall_score)

    weakness = detect_weaknesses(scores)

    score_columns = st.columns(4)

    with score_columns[0]:
        kpi_card("Overall score", f"{overall_score:.1f}/10", "Average of all evaluations")

    with score_columns[1]:
        kpi_card("Performance", performance, "Current level", "amber")

    with score_columns[2]:
        kpi_card("Evaluated responses", len(scores), "Scores recorded", "violet")

    with score_columns[3]:
        kpi_card(
            "Coaching questions",
            st.session_state.question_count,
            "Answered so far",
            "green",
        )

    st.markdown("")

    section_heading("Reasoning progress")

    if score_log:

        chart_columns = st.columns([3, 2])

        with chart_columns[0]:
            muted("Score per attempt, against the target of 7.")
            show_plotly(build_trend_figure(score_log))

        with chart_columns[1]:
            muted("Average score by module.")
            show_plotly(build_module_figure(score_log))

    else:

        notice(
            "info",
            "Complete coaching activities to generate your "
            "reasoning-performance charts.",
        )

    section_heading("Your reasoning profile")

    profile_columns = st.columns(2)

    with profile_columns[0]:

        render_html(
            f"""
            <div class="card">
                <div class="profile-label">Strongest area</div>
                <div class="profile-value">{esc(weakness["strongest"])}</div>
            </div>
            """
        )

    with profile_columns[1]:

        render_html(
            f"""
            <div class="card">
                <div class="profile-label">Area to improve</div>
                <div class="profile-value">{esc(weakness["weakest"])}</div>
            </div>
            """
        )

    section_heading("Coach insight")

    render_html(
        f"<div class='coach-insight'>{plain_html(weakness['insight'])}</div>"
    )

    st.markdown("")

    with st.expander("How CaseCraft stays reliable (and where it can fail)"):

        render_html(
            """
            <ul class="trust-list">
                <li><b>Input checks:</b> empty, very short or very long answers
                are stopped before they reach the AI.</li>
                <li><b>Instruction-override filter:</b> messages that try to
                change the coach's rules are rejected.</li>
                <li><b>Output checks:</b> empty or malformed AI responses are
                rejected, and errors stay visible instead of failing silently.</li>
                <li><b>Offline fallback:</b> Demo mode keeps the app usable when
                the AI service is down or rate-limited.</li>
                <li><b>Human judgement:</b> scores are coaching aids. The AI can
                misjudge reasoning, and the same answer can score differently
                between runs. Final grading stays with your instructor.</li>
                <li><b>Privacy:</b> in Live mode, case text and answers are sent
                to a third-party AI provider.</li>
            </ul>
            """
        )


# ============================================================
# FOOTER
# ============================================================

render_html(
    """
    <div class="footer">
        CaseCraft AI • MBA Case Reasoning Simulator
    </div>
    """
)