import streamlit as st

BG = "#0B0E14"
SURFACE = "#131720"
SURFACE_ALT = "#1B212C"
BORDER = "#262D3A"
TEXT = "#E6EDF3"
MUTED = "#8B96A5"

PRIMARY = "#A78BFA"

ACCENTS = {
    "generate": PRIMARY,
    "analyze": PRIMARY,
    "debug": PRIMARY,
}

PATHS = {
    "generate": "~/agents/generate.py",
    "analyze": "~/agents/analyze.py",
    "debug": "~/agents/debug.py",
}

PIXEL_FONT = "'Press Start 2P', monospace"


def inject_global_css():
    st.markdown(
        """
        <link rel="preconnect" href="https://fonts.googleapis.com">
        <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
        <link href="https://fonts.googleapis.com/css2?family=Press+Start+2P&family=JetBrains+Mono:wght@400;500;600;700&family=Inter:wght@400;500;600&display=swap" rel="stylesheet">
        """,
        unsafe_allow_html=True,
    )
    st.markdown(
        f"""
        <style>
        html, body, [class*="css"] {{
            font-family: 'Inter', sans-serif;
        }}

        .stApp {{
            background-color: {BG};
            background-image: radial-gradient({BORDER} 1px, transparent 1px);
            background-size: 22px 22px;
            color: {TEXT};
        }}

        section[data-testid="stSidebar"] {{
            background-color: {SURFACE};
            border-right: 1px solid {BORDER};
        }}

        h1, h2, h3, .stMarkdown h1, .stMarkdown h2, .stMarkdown h3 {{
            font-family: {PIXEL_FONT};
            color: {TEXT};
        }}

        div[data-testid="stVerticalBlockBorderWrapper"] {{
            background-color: {SURFACE};
            border: 1px solid {BORDER};
            border-radius: 10px;
        }}

        .stTextArea textarea, .stTextInput input {{
            background-color: {SURFACE_ALT};
            color: {TEXT};
            border: 1px solid {BORDER};
            font-family: 'JetBrains Mono', monospace;
        }}

        .stButton button {{
            font-family: 'JetBrains Mono', monospace;
            font-weight: 600;
            border-radius: 6px;
            border: 1px solid {BORDER};
            background-color: {SURFACE_ALT};
            color: {TEXT};
            transition: border-color 0.15s ease;
        }}

        .stButton button:hover {{
            border-color: {PRIMARY};
            color: {PRIMARY};
        }}

        pre, code {{
            font-family: 'JetBrains Mono', monospace !important;
        }}

        div[data-testid="stChatMessage"] {{
            background-color: {SURFACE_ALT};
            border: 1px solid {BORDER};
            border-radius: 8px;
        }}

        [data-testid="stFileUploader"] section {{
            background-color: {SURFACE_ALT};
            border: 1px dashed {BORDER};
            border-radius: 8px;
        }}

        .stTabs [data-baseweb="tab"] {{
            font-family: {PIXEL_FONT};
            font-size: 11px;
        }}

        header[data-testid="stHeader"] {{
            background-color: {BG} !important;
            background-image: radial-gradient({BORDER} 1px, transparent 1px) !important;
            background-size: 22px 22px !important;
        }}

        header[data-testid="stHeader"] > * {{
            background-color: transparent !important;
        }}

        [data-testid="stDeployButton"] {{
            display: none;
        }}

        [data-testid="stToolbarActions"] {{
            display: none;
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_page_header(title: str, tagline_lines: list, accent: str = PRIMARY):
    tagline_html = "<br/><br/>".join(tagline_lines)
    st.markdown(
        f"""
        <div style="
            font-family:{PIXEL_FONT};
            font-size:38px;
            line-height:1.4;
            color:{accent};
            text-shadow: 2px 2px 0 {BORDER};
            margin-bottom:10px;
        ">{title}</div>
        <div style="border-bottom:2px solid {accent}; margin-bottom:20px;"></div>
        <div style="
            background-color:{SURFACE};
            border:1px solid {BORDER};
            border-radius:10px;
            padding:20px 24px;
            font-style:italic;
            color:{TEXT};
            font-size:15px;
            margin-bottom:28px;
        ">{tagline_html}</div>
        """,
        unsafe_allow_html=True,
    )


def pixel_section_header(text: str, accent: str = PRIMARY):
    st.markdown(
        f"""
        <div style="
            font-family:{PIXEL_FONT};
            font-size:18px;
            color:{accent};
            margin:6px 0 16px;
        ">{text}</div>
        """,
        unsafe_allow_html=True,
    )


def pixel_label(text: str, color: str = MUTED, size: str = "11px"):
    st.markdown(
        f"""
        <div style="
            font-family:{PIXEL_FONT};
            color:{color};
            font-size:{size};
            margin-bottom:8px;
        ">{text}</div>
        """,
        unsafe_allow_html=True,
    )


def terminal_header(agent_key: str, label: str):
    accent = ACCENTS[agent_key]
    path = PATHS[agent_key]
    st.markdown(
        f"""
        <div style="
            background-color:{SURFACE_ALT};
            border:1px solid {BORDER};
            border-bottom:none;
            border-radius:10px 10px 0 0;
            padding:10px 16px;
            display:flex;
            align-items:center;
            gap:10px;
        ">
            <span style="width:11px;height:11px;border-radius:50%;background:#F97066;display:inline-block;"></span>
            <span style="width:11px;height:11px;border-radius:50%;background:#F5C451;display:inline-block;"></span>
            <span style="width:11px;height:11px;border-radius:50%;background:#4FD1C5;display:inline-block;"></span>
            <span style="
                font-family:'JetBrains Mono', monospace;
                color:{MUTED};
                font-size:13px;
                margin-left:8px;
            ">{path}</span>
            <span style="
                margin-left:auto;
                font-family:{PIXEL_FONT};
                color:{accent};
                font-size:10px;
                font-weight:400;
                border:1px solid {accent}55;
                background:{accent}18;
                padding:4px 10px;
                border-radius:20px;
            ">{label}</span>
        </div>
        """,
        unsafe_allow_html=True,
    )


def agent_panel(agent_key: str, label: str):
    terminal_header(agent_key, label)
    return st.container(border=True)