import re
import plotly.graph_objects as go


def extract_section(analysis, section_name, next_sections):

    pattern = rf"{re.escape(section_name)}\s*:?\s*(.*?)(?=\n(?:{'|'.join(map(re.escape, next_sections))})\s*:|\Z)"

    match = re.search(
        pattern,
        analysis,
        re.IGNORECASE | re.DOTALL
    )

    if not match:
        return ""

    text = match.group(1).strip()
    text = re.sub(r"\s+", " ", text)

    return text


def shorten(text, max_length=260):

    if not text:
        return "No information available."

    text = text.strip()

    if len(text) <= max_length:
        return text

    return text[:max_length - 3] + "..."


def create_case_map(analysis):

    sections = [
        "CASE TITLE",
        "COMPANY / ORGANIZATION",
        "INDUSTRY",
        "CENTRAL PROBLEM",
        "KEY DECISION TO BE MADE",
        "IMPORTANT FACTS",
        "KEY STAKEHOLDERS",
        "POSSIBLE ROOT CAUSES",
        "RELEVANT BUSINESS FRAMEWORKS",
        "IMPORTANT DATA / NUMBERS",
        "KEY TRADE-OFFS",
        "INFORMATION THAT IS MISSING",
        "POTENTIAL STRATEGIC OPTIONS"
    ]

    problem = extract_section(
        analysis,
        "CENTRAL PROBLEM",
        sections
    )

    decision = extract_section(
        analysis,
        "KEY DECISION TO BE MADE",
        sections
    )

    causes = extract_section(
        analysis,
        "POSSIBLE ROOT CAUSES",
        sections
    )

    options = extract_section(
        analysis,
        "POTENTIAL STRATEGIC OPTIONS",
        sections
    )

    tradeoffs = extract_section(
        analysis,
        "KEY TRADE-OFFS",
        sections
    )

    problem = shorten(problem)
    decision = shorten(decision)
    causes = shorten(causes)
    options = shorten(options)
    tradeoffs = shorten(tradeoffs)

    # --------------------------------------------------------
    # NODE POSITIONS
    # --------------------------------------------------------

    nodes = {
        "case": (0.50, 1.00),
        "problem": (0.50, 0.76),
        "causes": (0.22, 0.52),
        "decision": (0.78, 0.52),
        "options": (0.22, 0.27),
        "tradeoffs": (0.78, 0.27),
        "recommendation": (0.50, 0.05)
    }

    # --------------------------------------------------------
    # FIGURE
    # --------------------------------------------------------

    fig = go.Figure()

    # --------------------------------------------------------
    # CONNECTIONS
    # --------------------------------------------------------

    connections = [
        ("case", "problem"),
        ("problem", "causes"),
        ("problem", "decision"),
        ("causes", "options"),
        ("decision", "tradeoffs"),
        ("options", "recommendation"),
        ("tradeoffs", "recommendation")
    ]

    for start, end in connections:

        x1, y1 = nodes[start]
        x2, y2 = nodes[end]

        fig.add_trace(
            go.Scatter(
                x=[x1, x2],
                y=[y1, y2],
                mode="lines",
                line=dict(
                    width=2,
                    color="#CBD5E1"
                ),
                hoverinfo="none",
                showlegend=False
            )
        )

    # --------------------------------------------------------
    # CARD SHAPES
    # --------------------------------------------------------

    card_width = 0.30
    card_height = 0.13

    for x, y in nodes.values():

        fig.add_shape(
            type="rect",
            x0=x - card_width / 2,
            x1=x + card_width / 2,
            y0=y - card_height / 2,
            y1=y + card_height / 2,
            line=dict(
                color="#D1D5DB",
                width=1
            ),
            fillcolor="#FFFFFF",
            layer="below"
        )

    # --------------------------------------------------------
    # CARD TEXT
    # --------------------------------------------------------

    labels = {
        "case": "<b>CASE</b>",
        "problem": "<b>CENTRAL PROBLEM</b>",
        "causes": "<b>ROOT CAUSES</b>",
        "decision": "<b>KEY DECISION</b>",
        "options": "<b>STRATEGIC OPTIONS</b>",
        "tradeoffs": "<b>TRADE-OFFS</b>",
        "recommendation": "<b>RECOMMENDATION</b>"
    }

    for key, (x, y) in nodes.items():

        fig.add_annotation(
            x=x,
            y=y,
            text=labels[key],
            showarrow=False,
            font=dict(
                size=12,
                color="#111827"
            ),
            align="center",
            xanchor="center",
            yanchor="middle"
        )

    # --------------------------------------------------------
    # HOVER INFORMATION
    # --------------------------------------------------------

    hover_info = {
        "case": "Uploaded business case",

        "problem": (
            "<b>Central Problem</b><br><br>"
            + problem
        ),

        "causes": (
            "<b>Possible Root Causes</b><br><br>"
            + causes
        ),

        "decision": (
            "<b>Key Decision</b><br><br>"
            + decision
        ),

        "options": (
            "<b>Strategic Options</b><br><br>"
            + options
        ),

        "tradeoffs": (
            "<b>Key Trade-offs</b><br><br>"
            + tradeoffs
        ),

        "recommendation": (
            "<b>Recommendation</b><br><br>"
            "Your final recommendation should connect "
            "the problem, evidence, options and trade-offs."
        )
    }

    # Invisible hover points
    for key, (x, y) in nodes.items():

        fig.add_trace(
            go.Scatter(
                x=[x],
                y=[y],
                mode="markers",
                marker=dict(
                    size=35,
                    color="rgba(0,0,0,0)"
                ),
                hovertext=hover_info[key],
                hoverinfo="text",
                showlegend=False
            )
        )

    # --------------------------------------------------------
    # LAYOUT
    # --------------------------------------------------------

    fig.update_layout(
        title=dict(
            text="Case Decision Map",
            font=dict(
                size=20,
                color="#111827"
            ),
            x=0.02
        ),

        height=650,

        xaxis=dict(
            visible=False,
            range=[0, 1]
        ),

        yaxis=dict(
            visible=False,
            range=[-0.05, 1.10]
        ),

        plot_bgcolor="#F6F7F9",
        paper_bgcolor="#F6F7F9",

        margin=dict(
            l=40,
            r=40,
            t=80,
            b=30
        ),

        hoverlabel=dict(
            bgcolor="#111827",
            font=dict(
                color="#FFFFFF",
                size=12
            ),
            bordercolor="#111827"
        ),

        showlegend=False
    )

    return fig