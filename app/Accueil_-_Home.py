from pathlib import Path
import pandas as pd
import logging
import streamlit as st
from language_detection import detect_browser_language
from utils.i18n import load_content
from utils.language import normalize_language

st.set_page_config(page_title="Data Storytelling Dashboard", page_icon="📊", layout="wide")

with st.sidebar:
    st.header("Data Storytelling Dashboard")

### Language
try:
    browser_language = detect_browser_language()
except Exception:
    logging.getLogger(__name__).exception("Browser language detection failed")
    browser_language = None
with st.sidebar:
    choice = st.selectbox("Langue / Language", ["auto", "fr", "en"],
        format_func=lambda x: {"auto": "Automatique / Automatic", "fr": "Français", "en": "English"}[x],
        key="language_choice")
    st.divider()
lang = normalize_language(browser_language) if choice == "auto" else choice
t = load_content()[lang]


### PATH & DATA

data_path = Path("data/resultats-par-niveau-dpt-t1-france-entiere.txt")
if data_path.exists():
    grades_df = pd.read_csv(data_path, delimiter=";")
else:
    st.warning("# data inexistant #")
    st.stop()

profile_picture_path = Path("assets/Photo Arthur Donnat.jpg")
efrei_logo_path = Path("assets/LOGO-EFREI.png")


### NAVIGATION

with st.sidebar:
    st.divider()
    st.title("Home Navigation:")
    st.markdown("[Profil](#profil)")
    st.divider()


### PROFILE & Social medias

if efrei_logo_path.exists():
    st.image(efrei_logo_path)
else:
    st.warning("# Logo EFREI inexistant #")


st.markdown('<div id="profil"></div>', unsafe_allow_html=True)
left, right = st.columns([1, 3], vertical_alignment="center")
with left:
    if profile_picture_path.exists():
        st.image(profile_picture_path)
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
        </style>
        """, unsafe_allow_html=True)
    st.markdown(f"""
        <div class="hero">
          <p>{t["dashboard_title"]}</p>
          <h2>Arthur DONNAT</h2>
          <h3>Étudiant ingénieur à l'EFREI - Majeure Data and IA</h3>
          <p>Email: arthur.donnat@efrei.net</p>
          <p>2026</p>
        </div>
        """, unsafe_allow_html=True)
    social_links = [
        ("LinkedIn", "www.linkedin.com/in/arthur-donnat", "https://cdn.simpleicons.org/linkedin/0A66C2"),
        ("GitHub", "https://github.com/Miner205", "https://cdn.simpleicons.org/github/FFFFFF"),
    ]
    for label, url, icon_url in social_links:
        st.markdown(
            f'<a href="{url}" target="_blank" style="display:flex;align-items:center;gap:12px;'
            f'padding:9px 12px;margin:6px 0;border:1px solid rgba(128,128,128,.25);'
            f'border-radius:12px;">'
            f'<img src="{icon_url}" width="24" height="24" alt="{label} logo">'
            f'<span>{label}</span><span style="margin-left:auto;">↗</span></a>',
            unsafe_allow_html=True
        )
    st.divider()
    st.write("Data Analysis & Visualization")
    st.write("Teachers: DOUBLIER Sophie & MATHEW Mano Joseph")
    st.divider()
    st.subheader(f"Project: {t["dashboard_title"]}")
    st.markdown("Proposed by: [MATHEW Mano Joseph](mano.mathew@efrei.fr)")

st.divider()


st.subheader(t["home_title"])
st.write(t["intro"])

st.header(t["brief_title"])
for item in t["brief"]:
    st.markdown(f"- {item}")
st.subheader(t["rubric_title"])
for item in t["rubric"]:
    st.write(f'{item["criterion"]} — {item["points"]}/100')
st.subheader(t["deliverables_title"])
for item in t["deliverables"]:
    st.markdown(f"- {item}")
st.caption(t["footer"])


st.divider()
st.divider()

for col, label, value in zip(st.columns(3), t["metrics"], ["≥ 3", "2–4 min", "100"]):
    col.metric(label, value)
st.caption("Objectifs du livrable final — pas des résultats du dataset." if lang == "fr" else "Final deliverable targets — not dataset results.")

project, requirements, grading, deliverables, roadmap = st.tabs(t["tabs"])
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
    for label, points, detail in t["rubric"]:
        with st.container(border=True):
            left, right = st.columns([4, 1])
            left.subheader(label)
            left.write(detail)
            right.metric("Points", f"{points}/100")
            st.progress(points / 100)
with deliverables:
    st.header(t["package"])
    for item in t["deliverables"]:
        st.markdown(f"- {item}")
    st.code("StApp26_20000_NOM_DAI.zip", language=None)
    st.caption(t["naming"])
    st.write(t["packaging"])
    st.subheader(t["check_title"])
    st.caption(t["check_note"])
    # Explicit values persist across language switches within this session only.
    for i, label in enumerate(t["checks"]):
        stable_key = f"check_value_{i}"
        if stable_key not in st.session_state:
            st.session_state[stable_key] = False
        selected = st.checkbox(label, value=st.session_state[stable_key], key=f"check_{lang}_{i}")
        st.session_state[stable_key] = selected
with roadmap:
    st.header(t["road_title"])
    st.info(t["road_note"])
    for i, (title, body) in enumerate(t["road"], 1):
        with st.container(border=True):
            st.subheader(f"{i:02d} · {title}")
            st.write(body)
    st.write(t["next"])

st.divider()
st.caption(t["footer"])
with st.expander(t["links"]):
    st.markdown("- [Streamlit](https://docs.streamlit.io/)\n- [Streamlit Browser Language Detector](https://github.com/louisoutin/streamlit-browser-language)")
