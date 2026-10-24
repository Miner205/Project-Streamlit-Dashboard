from pathlib import Path
import logging
import pandas as pd
import streamlit as st
from language_detection import detect_browser_language
from utils.i18n import load_content, normalize_language
from utils.parser import parse_results
from utils.geo import GEO_SOURCE, GEO_ATTRIBUTION, filter_by_territory, load_departements_geo, show_geo_credit, territory_filter, ELECTION_TO_INSEE, NON_CARTOGRAPHIABLE


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


### geo data load
geo = load_departements_geo()



st.title(t["dashboard_title"])
st.markdown(f":small[Dataset {t["source"].lower()}: Election présidentielle des 10 et 24 avril 2022 - Résultats définitifs du 1er tour - par département — [{t["source"]}]({SOURCE}) — License Not Specified]")
st.divider()


### content of the page
st.header(t["quality_title"])
st.write(t["quality_intro"])
a, b, c = st.columns(3)
a.metric(t["rows"], len(departments))
b.metric(t["encoding"], report["encoding"])
missing = int(departments.isna().sum().sum() + candidates.isna().sum().sum())
c.metric(t["missing"], missing)
for item in t["quality_checks"]:
    st.markdown(f"- {item}")
if report["issues"]:
    st.warning(t["quality_bad"])
    with st.expander(t["quality_details"], expanded=True):
        for issue in report["issues"]:
            st.write(issue)
else:
    st.success(t["quality_ok"])
st.caption(t["license"])

st.divider()


### geo
st.subheader("Contrôle de la jointure géographique")

if geo is None:
    st.error(f"{t["map_missing_shapefile"]}")
else:
    election_codes = set(departments["code"].astype(str).str.upper())
    geo_codes = set(geo["geo_code"])
    mapped_codes = {
        ELECTION_TO_INSEE.get(code, code)
        for code in election_codes
        if code not in NON_CARTOGRAPHIABLE
    }

    missing_in_geo = sorted(mapped_codes - geo_codes)
    non_mapped = sorted(election_codes & NON_CARTOGRAPHIABLE.keys())

    col1, col2, col3 = st.columns(3)
    col1.metric("Départements électoraux", len(election_codes))
    col2.metric("Départements cartographiables", len(mapped_codes))
    col3.metric("Territoires sans contour OSM", len(non_mapped))

    if missing_in_geo:
        st.warning(
            "Départements cartographiables absents des contours : "
            + ", ".join(missing_in_geo)
        )
    else:
        st.success(
            "Tous les départements et DOM cartographiables sont appariés aux contours OSM."
        )

    with st.expander(t["geo_quality_method"], expanded=False):
        for text in t["geo_quality_method_text"]:
            st.markdown(text)
        st.markdown(
            f"""
            **{t["geo_overseas_mapping"]}**\n
            {t["geo_overseas_mapping_text"]}\n
            **{t["geo_non_cartographic"]}**\n
            {t["geo_non_cartographic_text"]}\n
            """
        )
        mapping_df = pd.DataFrame(
            [
                {
                    "Code électoral 2022": election_code,
                    "Code INSEE / OSM": insee_code,
                    "Territoire": territory_name,
                }
                for election_code, insee_code in ELECTION_TO_INSEE.items()
                for territory_name in [
                "Guadeloupe" if election_code == "ZA"
                else "Martinique" if election_code == "ZB"
                else "Guyane" if election_code == "ZC"
                else "La Réunion" if election_code == "ZD"
                else "Mayotte"]
            ]
        )
        st.dataframe(
            mapping_df,
            use_container_width=True,
            hide_index=True,
        )

    with st.expander("Territoires non cartographiables", expanded=False):
        st.markdown(
            f"""
            {t["geo_non_cart"]}
            - `ZN` — Nouvelle-Calédonie  
            - `ZP` — Polynésie française  
            - `ZS` — Saint-Pierre-et-Miquelon  
            - `ZW` — Wallis-et-Futuna  
            - `ZX` — Saint-Martin / Saint-Barthélemy  
            - `ZZ` — Français établis hors de France  
            {t["non_cartographic_warning"]}
            """
        )
st.subheader("Licences et attribution")
st.markdown(
    f"""
    - **Résultats électoraux :** [data.gouv.fr]({SOURCE}).
    - **Contours départementaux :** [OpenStreetMap via data.gouv.fr]({GEO_SOURCE}).
    - **Attribution obligatoire :** {GEO_ATTRIBUTION}.
    - **Licence des contours :** ODbL, avec partage à l’identique.
    """
)
show_geo_credit(t)
