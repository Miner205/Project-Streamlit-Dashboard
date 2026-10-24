from pathlib import Path
import logging
import pandas as pd
import plotly.express as px
import streamlit as st
from language_detection import detect_browser_language
from utils.i18n import load_content, normalize_language
from utils.parser import parse_results
from utils.geo import department_map, filter_by_territory, load_departements_geo, show_geo_credit, territory_filter, NON_CARTOGRAPHIABLE


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

# filters
with st.sidebar:
    st.header(t["filters"])
    territory = territory_filter(f"{t["territory_filter"]}")
    departments_filtered = filter_by_territory(departments, territory)
    codes = st.multiselect(
        t["departments"],
        departments_filtered["code"].tolist(),
        default=departments_filtered["code"].tolist(),
        format_func=lambda code: (
            code + " - "
            + departments_filtered.set_index("code").loc[code, "department"]
        ),
    )
    names = sorted(candidates["candidate"].unique())
    chosen = st.multiselect(t["candidates"], names, default=names)
if not codes or not chosen:
    st.warning(t["empty"])
    st.stop()
d = departments[departments["code"].isin(codes)].copy()
all_c = candidates[candidates["code"].isin(codes)].copy()
c = all_c[all_c["candidate"].isin(chosen)].copy()

registered=int(d["registered"].sum())
voters=int(d["voters"].sum())
valid=int(d["valid"].sum())
st.title(t["eda_title"])
st.caption(t["selected"])
if report["issues"]:
    st.warning(t["quality_bad"])
for col,label,value in zip(st.columns(3),t["kpis"],[f"{registered:,}",f"{100*voters/registered:.2f} %" if registered else "—",f"{valid:,}"]):
    col.metric(label,value)
# Candidate filtering never changes turnout or the valid-vote denominator.
st.caption("Le filtre candidat ne change pas la participation ni le dénominateur des scores." if lang=="fr" else "Candidate selection does not change turnout or vote-share denominators.")
d["turnout_pct"] = 100 * d["voters"].div(d["registered"].replace(0, float("nan")))


st.subheader(t["tables"][0])
st.dataframe(d, hide_index=True)
st.subheader(t["tables"][1])
st.dataframe(c, hide_index=True)


### geo
st.subheader(f"{t["map_turnout_title"]}")
participation_map = department_map(t,
    geo,
    d[["code", "turnout_pct"]],
    color_label="Participation (%)",
    territory=territory,
    color_scale="Viridis",
    hover_data={"turnout_pct": ":.2f"},
)
if participation_map is not None:
    st.plotly_chart(participation_map)
    st.write(f"{t["map_turnout_help"]}")


### non cartographiable
st.divider()
st.subheader(t["non_cartographic_title"])
st.write(t["non_cartographic_intro"])
st.info(t["non_cartographic_warning"])

non_cartographic_codes = list(NON_CARTOGRAPHIABLE.keys())

nc_departments = departments[
    departments["code"].astype(str).str.upper().isin(non_cartographic_codes)
].copy()

nc_candidates = candidates[
    candidates["code"].astype(str).str.upper().isin(non_cartographic_codes)
].copy()

if nc_departments.empty:
    st.info(t["map_no_data"])
else:
    nc_departments["turnout_pct"] = 100 * nc_departments["voters"].div(
        nc_departments["registered"].replace(0, float("nan"))
    )

    registered = int(nc_departments["registered"].sum())
    valid = int(nc_departments["valid"].sum())

    k1, k2, k3 = st.columns(3)
    k1.metric(t["non_cartographic_kpi_registered"], f"{registered:,}")
    k2.metric(
        t["non_cartographic_kpi_turnout"],
        f"{100 * voters / registered:.2f} %" if registered else "—",
    )
    k3.metric(t["non_cartographic_kpi_valid"], f"{valid:,}")

    st.subheader(t["non_cartographic_table_title"])

    territory_names = nc_departments["code"].map(NON_CARTOGRAPHIABLE)

    nc_table = nc_departments[
        ["code", "department", "registered", "voters", "valid", "turnout_pct"]
    ].copy()
    nc_table["territory"] = territory_names

    st.dataframe(
        nc_table.rename(
            columns={
                "code": "Code électoral",
                "territory": "Territoire",
                "department": "Libellé officiel",
                "registered": "Inscrits",
                "voters": "Votants",
                "valid": "Suffrages exprimés",
                "turnout_pct": "Participation (%)",
            }
        ),
        hide_index=True,
    )

    labels = {
        "territory": t["territory_filter"],
        "turnout_pct": t["turnout"],
        "valid": t["votes"],
    }

    st.subheader(t["non_cartographic_turnout_title"])
    st.plotly_chart(
        px.bar(
            nc_table.sort_values("turnout_pct"),
            x="turnout_pct",
            y="territory",
            orientation="h",
            labels=labels,
            text="turnout_pct",
        ).update_traces(texttemplate="%{text:.2f} %", textposition="outside"),
    )

    st.subheader(t["non_cartographic_votes_title"])
    st.plotly_chart(
        px.bar(
            nc_table.sort_values("valid"),
            x="valid",
            y="territory",
            orientation="h",
            labels=labels,
            text="valid",
        ).update_traces(texttemplate="%{text:,}", textposition="outside"),
    )

    st.subheader(t["non_cartographic_candidate_title"])
    st.caption(t["non_cartographic_candidate_help"])

    candidate_scores = (
        nc_candidates.merge(
            nc_departments[["code", "valid"]],
            on="code",
            validate="many_to_one",
        )
    )
    candidate_scores["share"] = 100 * candidate_scores["votes"].div(
        candidate_scores["valid"].replace(0, float("nan"))
    )

    candidate_mean = (
        candidate_scores
        .groupby("candidate", as_index=False)["share"]
        .mean()
        .sort_values("share", ascending=False)
    )

    st.plotly_chart(
        px.bar(
            candidate_mean,
            x="share",
            y="candidate",
            orientation="h",
            labels={
                "candidate": t["candidate"],
                "share": t["score"],
            },
            text="share",
        ).update_traces(texttemplate="%{text:.2f} %", textposition="outside"),
    )


show_geo_credit(t)
