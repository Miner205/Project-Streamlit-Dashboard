from pathlib import Path
import logging
import pandas as pd
import streamlit as st
from language_detection import detect_browser_language
from utils.i18n import load_content, normalize_language
from utils.parser import parse_results
from utils.geo import GEO_SOURCE, load_departements_geo, show_geo_credit, ELECTION_TO_INSEE


SOURCE = "https://www.data.gouv.fr/datasets/election-presidentielle-des-10-et-24-avril-2022-resultats-definitifs-du-1er-tour"
DEFAULT_PATH = Path("data/resultats-par-niveau-dpt-t1-france-entiere.txt")

st.set_page_config(page_title="Dashboard Présidentielle 2022", page_icon="🗳️", layout="wide")

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


### Upload own/custom file
initial_state = {
    "dataset_bytes": None,
    "dataset_filename": None,
    "dataset_source": SOURCE,
    "dataset_upload_version": 0,
}
for key, value in initial_state.items():
    if key not in st.session_state:
        st.session_state[key] = value

def return_to_default():
    """Discard a custom dataset and reset the upload widget."""
    st.session_state["dataset_bytes"] = None
    st.session_state["dataset_filename"] = DEFAULT_PATH.name
    st.session_state["dataset_source"] = SOURCE
    # A new key creates an empty uploader on the next run.
    st.session_state["dataset_upload_version"] += 1

def remember_upload(widget_key):
    """Copy an uploaded file into independent application state."""
    file = st.session_state.get(widget_key)

    if file is not None:
        st.session_state["dataset_bytes"] = file.getvalue()
        st.session_state["dataset_filename"] = file.name
        st.session_state["dataset_source"] = "custom source"
    else:
        # Clicking the uploader's own X also returns to the default.
        return_to_default()

upload_key = (
    f"_dataset_upload_"
    f"{st.session_state['dataset_upload_version']}"
)

with st.sidebar:
    st.file_uploader(t["upload"],
                     type=["txt","csv"],
                     key=upload_key,
                     on_change=remember_upload,
                     args=(upload_key,))
    st.button(
        t["unload_dataset"],
        key="unload_dataset_button",
        on_click=return_to_default,
        disabled=(
                st.session_state["dataset_source"] != "custom source"
        ),
        help=t["unload_dataset_help"],
    )
    if st.session_state["dataset_filename"]:
        st.caption(
            f"📄 {st.session_state['dataset_filename']}"
        )


### Load dataset
@st.cache_data(show_spinner=False)
def load_results(raw):
    departments, candidates, report = parse_results(raw)
    return pd.DataFrame(departments), pd.DataFrame(candidates), report

if st.session_state.get("dataset_bytes") is None:
    print(DEFAULT_PATH)
    if not DEFAULT_PATH.exists():
        st.error(f"{t['default_file_error']}: {DEFAULT_PATH.name}")
        st.stop()
    st.session_state["dataset_bytes"] = DEFAULT_PATH.read_bytes()
    st.session_state["dataset_filename"] = DEFAULT_PATH.name
    st.session_state["dataset_source"] = SOURCE
with st.sidebar:
    if st.session_state["dataset_source"] != "custom source":
        st.caption(t["default_dataset"])
        st.markdown(f':small[[{t["source"]}]({SOURCE})]')
    else:
        st.caption(t["custom_dataset"])
try:
    departments, candidates, report = load_results(st.session_state.get("dataset_bytes"))
except ValueError as exc:
    st.error(f'{t["error"]}: {exc}')
    if st.session_state["dataset_source"] == "custom source":
        st.info(t["invalid_custom_dataset"])
    else:
        st.info(t["invalid_default_dataset"])
    st.stop()


st.title(t["dashboard_title"])
st.markdown(f":small[Dataset {t["source"].lower()}: Election présidentielle des 10 et 24 avril 2022 - Résultats définitifs du 1er tour - par département — [{t["source"]}]({SOURCE}) — License Not Specified]")
st.divider()


### content of the page
st.header(t["story_title"])
st.markdown(f"**{t["my_question"]}**")
st.write(t["audience"])
st.write(t["takeaways"])
for item in t["story"]:
    st.markdown(f"- {item}")

if st.session_state["dataset_source"] != "custom source":
    st.caption(t["default_dataset"])
    st.markdown(f':small[[{t["source"]}]({SOURCE})]')
    st.info(t["custom_file_info"])
else:
    st.caption(t["custom_dataset"])


st.caption(t["license"])




### geo
st.subheader(t["geo_title"])
st.write(t["geo"])
st.write(t["geo_intro"])

geo = load_departements_geo()

if geo is None:
    st.warning(f"{t["map_missing_shapefile"]}")
else:
    col1, col2, col3 = st.columns([2, 3, 3])
    col1.metric(f"{t['mapped_dep']}", len(geo))
    col2.metric(f"{t['geo_reference_date']}", f"{t['geo_reference_value']}")
    col3.metric(f"{t['geo_projection']}", f"{t['geo_projection_value']}")

    with st.expander(t["geo_dataset_title"], expanded=False):
        st.markdown(f"- **{t['geo_source']} :** [data.gouv.fr]({GEO_SOURCE})")
        st.markdown(f"- **{t['geo_reference_date']} :** {t['geo_reference_value']}")
        st.markdown(f"- **{t['geo_projection']} :** {t['geo_projection_value']}")
        st.markdown(f"- **{t['geo_join_key']} :** {t['geo_join_value']}")
        st.markdown(f"- **{t['geo_attributes']} :** {t['geo_attributes_value']}")
        st.markdown(f"- **{t['geo_coverage']} :** {t['geo_coverage_value']}")
        st.markdown(f"- **{t['geo_license']} :** ODbL — {t['geo_attribution']}")

        st.info(t["geo_compatibility_text"])
        st.warning(t["geo_overseas_mapping_text"])

        ## geo tableau:
        geo_table = geo.drop(columns="geometry", errors="ignore").copy()
        # Ajout du code électoral correspondant, lorsque la correspondance existe.
        insee_to_election = {v: k for k, v in ELECTION_TO_INSEE.items()}
        geo_table["election_code"] = geo_table["geo_code"].map(insee_to_election)
        # Les départements métropolitains et la Corse gardent le même code.
        geo_table["election_code"] = geo_table["election_code"].fillna(
            geo_table["geo_code"]
        )
        geo_table = geo_table.rename(
            columns={
                "geo_code": "Code INSEE / OSM",
                "election_code": "Code électoral 2022",
                "department": "Département",
                "nuts3": "NUTS3",
                "wikidata": "Wikidata",
                "area_km2": "Surface (km²)",
            }
        )
        # Colonnes optionnelles : on ne garde que celles réellement disponibles.
        possible_columns = [
            "Code électoral 2022",
            "Code INSEE / OSM",
            "Département",
            "NUTS3",
            "Wikidata",
            "Surface (km²)",
        ]
        available_columns = [
            col for col in possible_columns if col in geo_table.columns
        ]
        st.dataframe(
            geo_table[available_columns],
            hide_index=True,)
        #todo: why is the fucking col "Wikidata" disappearing ?? (it was working fine before putting the 2 codes) - eh whatever..."

show_geo_credit(t)
