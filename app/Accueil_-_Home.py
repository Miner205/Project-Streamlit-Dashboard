from math import ceil, floor
from pathlib import Path
import logging
import streamlit as st
from language_detection import detect_browser_language
from utils.i18n import load_content
from utils.language import normalize_language

st.set_page_config(page_title="Data Storytelling Dashboard", page_icon="📊", layout="wide")

with st.sidebar:
    st.header("Data Storytelling Dashboard")

### Language
if "language_mode" not in st.session_state:
    st.session_state["language_mode"] = "auto"

try:
    browser_language = detect_browser_language()
except Exception:
    logging.getLogger(__name__).exception("Browser language detection failed")
    browser_language = None

# Remember the browser language once the component returns a value.
# A temporary None on a later rerun must not reset it.
if isinstance(browser_language, str) and browser_language.strip():
    st.session_state["app_detected_language"] = normalize_language(browser_language)

def save_language_mode():
    st.session_state["language_mode"] = (
        st.session_state["_language_mode_widget"]
    )

# Restore the widget from the persistent application value.
st.session_state["_language_mode_widget"] = (
    st.session_state["language_mode"]
)

with st.sidebar:
    choice = st.selectbox("Langue / Language", ["auto", "fr", "en"],
        format_func=lambda x: {"auto": "Automatique / Automatic", "fr": "Français", "en": "English"}[x],
        key="_language_mode_widget", on_change=save_language_mode)
    st.divider()
mode = st.session_state["language_mode"]
lang = (
    st.session_state.get("app_detected_language", "en")
    if mode == "auto"
    else mode
)
st.session_state["language"] = lang
t = load_content()[lang]


### NAVIGATION

with st.sidebar:
    st.title("Home Navigation:")
    st.markdown("[Profil](#profil)")
    st.divider()


### PROFILE & Social medias
st.markdown('<div id="profil"></div>', unsafe_allow_html=True)
profile_picture_path = Path("assets/Photo Arthur Donnat.jpg")
efrei_logo_path = Path("assets/LOGO-EFREI.png")
left, right = st.columns([1, 3])
with left:
    _, smaller_efrei_logo, _ = st.columns([1, 3, 1])
    with smaller_efrei_logo:
        if efrei_logo_path.exists():
            st.image(efrei_logo_path, alt="EFREI Logo")
        else:
            st.warning("# Logo EFREI inexistant #")
    if profile_picture_path.exists():
        st.image(profile_picture_path, alt="Arthur Donnat Photo/Picture")
    else:
        st.warning("# Photo de profil inexistante #")
with right:
    st.markdown("""
        <style>
            .hero {
                padding: 1.8rem; border-radius: 22px;
                background: linear-gradient(135deg, #111827 0%, #1e3a5f 60%, #2563eb 100%);
                color: white; margin-bottom: 1rem;
            }
            .hero p {font-size: 1.08rem; opacity: .9;}
            .hero h1 {font-size: 2.2rem; margin-bottom: .25rem;}
        </style>
        """, unsafe_allow_html=True)
    st.markdown(f"""
        <div class="hero">
          <h1>{t["dashboard_title"]}</h1>
          <h2>Arthur DONNAT</h2>
          <h3>Étudiant ingénieur à l'EFREI - Majeure Data and IA</h3>
          <p>Email: arthur.donnat@efrei.net</p>
          <p>2026</p>
        </div>
        """, unsafe_allow_html=True)
    social_links = [
        ("LinkedIn", "https://www.linkedin.com/in/arthur-donnat", "https://img.icons8.com/color/48/linkedin.png"),
        ("GitHub", "https://github.com/Miner205", "https://img.icons8.com/ios-glyphs/48/24292e/github.png"),
    ]
    smaller_linkedin_github = st.columns([1, 1])
    i = 0
    for label, url, icon_url in social_links:
        with smaller_linkedin_github[i]:
            st.markdown(
                f'<a href="{url}" target="_blank" style="display:flex;align-items:center;gap:12px;'
                f'padding:9px 12px;margin:6px 0;border:1px solid rgba(128,128,128,.25);'
                f'border-radius:12px;">'
                f'<img src="{icon_url}" width="24" height="24" alt="{label} logo">'
                f'<span>{label}</span><span style="margin-left:auto;">↗</span></a>',
                unsafe_allow_html=True
            )
        i += 1
    st.divider()
    st.write("Course: Data Analysis & Visualization")
    st.write("Teachers: DOUBLIER Sophie & MATHEW Mano Joseph")
    st.markdown("Project Proposed by: [MATHEW Mano Joseph](mano.mathew@efrei.fr)")

st.divider()


### content of the page
st.header(t["home_title"])
st.subheader(t["home_subtitle"])
st.write(t["intro"])

st.header(t["brief_title"])

project, requirements, grading, deliverables = st.tabs(t["tabs"])
with project:
    st.header(t["question"])
    st.write(t["project"])
    for start in (0, 2):
        for col, (title, body) in zip(st.columns(2), t["arc"][start:start+2]):
            with col.container(border=True):
                st.subheader(title)
                st.write(body)
    st.subheader(t["portals"])
    st.write(t["source_rule"])
    st.markdown("- [data.gouv.fr](https://www.data.gouv.fr/datasets)\n- [GD4H](https://gd4h.ecologie.gouv.fr/en/catalogue)\n- [data.europa.eu](https://data.europa.eu/data/combined?locale=en)")
    with st.expander(t["selection"], expanded=True):
        for item in t["selection_items"]:
            st.markdown(f"- {item}")
    st.subheader(t["patterns"])
    st.write(t["pattern_text"])
with requirements:
    st.header(t["req_title"])
    for title, items in t["req_groups"]:
        with st.expander(title, expanded=True):
            for item in items:
                st.markdown(f"- {item}")
with grading:
    st.header(t["rubric_title"])
    j = 0
    rubric_cols = [st.columns([1, 1]) for _ in range(ceil(len(t["rubric"])/2))]
    for label, points, detail in t["rubric"]:
        with rubric_cols[floor(j//2)][j%2]:
            with st.container(border=True):
                left, right = st.columns([4, 1])
                left.subheader(f"{j+1}. "+label)
                left.write(detail)
                right.metric("Points", f"{points}/100")
                st.progress(points / 100)
        j += 1
with deliverables:
    st.header(t["deliverables_title"])
    for item in t["deliverables"]:
        st.markdown(f"- {item}")
    st.caption(t["naming"])
    st.write(t["packaging"])

st.divider()
st.caption(t["footer"])
with st.expander(t["links"]):
    st.markdown("- [Streamlit](https://docs.streamlit.io/)\n- [Streamlit Browser Language Detector](https://github.com/louisoutin/streamlit-browser-language)")
