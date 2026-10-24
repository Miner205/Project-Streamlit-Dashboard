from pathlib import Path
import logging
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import missingno as msno
import matplotlib.pyplot as plt
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


### Quality-control helpers
def count_duplicate_rows(df, subset=None):
    """Nombre de lignes entièrement ou partiellement dupliquées."""
    if subset is None:
        return int(df.duplicated().sum())
    return int(df.duplicated(subset=subset).sum())

def duplicate_examples(df, subset=None):
    """Retourne les premières lignes dupliquées pour inspection."""
    mask = df.duplicated(subset=subset, keep=False)
    return df.loc[mask].head(20)

def numeric_correlation_matrix(df, exclude=None):
    """Matrice de corrélation des colonnes numériques pertinentes."""
    exclude = exclude or set()
    numeric_df = (
        df.select_dtypes(include=[np.number])
        .drop(columns=[col for col in exclude if col in df.columns], errors="ignore")
    )
    return numeric_df.corr(numeric_only=True)

def plot_correlation_matrix(corr, title):
    """Heatmap Plotly d’une matrice de corrélation."""
    fig = px.imshow(
        corr,
        text_auto=".2f",
        aspect="auto",
        color_continuous_scale="RdBu_r",
        zmin=-1,
        zmax=1,
        title=title,
    )
    fig.update_layout(
        height=620,
        margin={"r": 20, "t": 60, "l": 20, "b": 20},
        coloraxis_colorbar={"title": "Corrélation"},
    )
    return fig

def election_consistency_checks(departments, candidates):
    """Contrôles métier du fichier présidentiel par département."""
    checks = []

    # 1. Unicité des codes départementaux.
    duplicate_department_codes = count_duplicate_rows(
        departments,
        subset=["code"],
    )
    checks.append(
        {
            "label": t["quality_check_unique_codes"],
            "passed": duplicate_department_codes == 0,
            "detail": f"{duplicate_department_codes} code(s) départemental(aux) dupliqué(s).",
        }
    )

    # 2. Cohérence horizontale : inscrits >= votants >= exprimés.
    invalid_turnout_chain = departments[
        (departments["registered"] < departments["voters"])
        | (departments["voters"] < departments["valid"])
    ]
    checks.append(
        {
            "label": t["quality_check_turnout_chain"],
            "passed": invalid_turnout_chain.empty,
            "detail": f"{len(invalid_turnout_chain)} département(s) concerné(s).",
        }
    )

    # 3. Pas de valeurs négatives dans les volumes électoraux.
    volume_columns = [
        col for col in ["registered", "voters", "valid"]
        if col in departments.columns
    ]
    negative_volumes = departments[
        (departments[volume_columns] < 0).any(axis=1)
    ] if volume_columns else departments.iloc[0:0]
    checks.append(
        {
            "label": t["quality_check_non_negative"],
            "passed": negative_volumes.empty,
            "detail": f"{len(negative_volumes)} département(s) concerné(s).",
        }
    )

    # 4. Somme des voix candidates proche des suffrages exprimés.
    votes_by_department = (
        candidates.groupby("code", as_index=False)["votes"].sum()
        .rename(columns={"votes": "candidate_votes_total"})
    )
    vote_check = departments.merge(
        votes_by_department,
        on="code",
        how="left",
        validate="one_to_one",
    )
    vote_check["vote_gap"] = (
        vote_check["candidate_votes_total"] - vote_check["valid"]
    )
    inconsistent_votes = vote_check[
        vote_check["vote_gap"].abs() > 1
    ]
    checks.append(
        {
            "label": t["quality_check_vote_sum"],
            "passed": inconsistent_votes.empty,
            "detail": (
                f"{len(inconsistent_votes)} département(s) avec un écart "
                "supérieur à 1 voix."
            ),
        }
    )

    # 5. Chaque département possède le même nombre de candidats.
    candidates_per_department = (
        candidates.groupby("code")["candidate"].nunique()
    )
    inconsistent_candidate_counts = (
        candidates_per_department.nunique() != 1
    )
    checks.append(
        {
            "label": t["quality_check_candidate_count"],
            "passed": not inconsistent_candidate_counts,
            "detail": (
                f"{candidates_per_department.nunique()} nombre(s) différent(s) "
                "de candidats observé(s)."
            ),
        }
    )
    # 6. Pas de score négatif.
    negative_scores = candidates[candidates["votes"] < 0]
    checks.append(
        {
            "label": t["quality_check_candidate_scores"],
            "passed": negative_scores.empty,
            "detail": f"{len(negative_scores)} ligne(s) concernée(s).",
        }
    )
    return checks, vote_check


st.title(t["dashboard_title"])
st.markdown(f":small[Dataset {t["source"].lower()}: Election présidentielle des 10 et 24 avril 2022 - Résultats définitifs du 1er tour - par département — [{t["source"]}]({SOURCE}) — License Not Specified]")
st.divider()


### content of the page
st.header(t["quality_title"])
st.write(t["quality_intro"])


dept_duplicate_rows = count_duplicate_rows(departments)
cand_duplicate_rows = count_duplicate_rows(candidates)

dept_duplicate_codes = count_duplicate_rows(departments, subset=["code"])
cand_duplicate_keys = count_duplicate_rows(
    candidates,
    subset=["code", "candidate"],
)

missing_departments = int(departments.isna().sum().sum())
missing_candidates = int(candidates.isna().sum().sum())

a, b, c, d = st.columns(4)
a.metric(t["rows"], len(departments))
b.metric(t["encoding"], report["encoding"])
c.metric(
    t["duplicates"][0],
    f"{dept_duplicate_rows} / {dept_duplicate_codes}",
    help=t["duplicates_help"][0],
)
d.metric(
    t["duplicates"][1],
    f"{cand_duplicate_rows} / {cand_duplicate_keys}",
    help=t["duplicates_help"][1],
)

e, f, g = st.columns(3)
e.metric(t["missings"][0], missing_departments)
f.metric(t["missings"][1], missing_candidates)
g.metric(
    t["missings"][2],
    missing_departments + missing_candidates,
)


for item in t["quality_checks"]:
    st.markdown(f"- {item}")
if report["issues"]:
    st.warning(t["quality_bad"])
    with st.expander(t["quality_details"], expanded=True):
        for issue in report["issues"]:
            st.write(issue)
else:
    st.success(t["quality_ok"])


## missingno
st.subheader(' '.join(t["missings"][0].split(' ')[:-1])+' - missingno')
st.caption(t["quality_missingno_caption"])

tab_missing_dept, tab_missing_cand = st.tabs([
    "Départements",
    "Candidats",
])

with tab_missing_dept:
    st.caption("Matrix plot des valeurs manquantes dans le tableau départemental.")
    fig_dept, ax_dept = plt.subplots(figsize=(10, 4))
    msno.matrix(departments, ax=ax_dept, sparkline=False)
    st.pyplot(fig_dept)
    plt.close(fig_dept)

    st.caption("Fréquence des valeurs présentes par colonne.")
    fig_dept_bar, ax_dept_bar = plt.subplots(figsize=(10, 3))
    msno.bar(departments, ax=ax_dept_bar, sort="descending")
    st.pyplot(fig_dept_bar)
    plt.close(fig_dept_bar)

with tab_missing_cand:
    st.caption("Matrix plot des valeurs manquantes dans le tableau des candidats.")
    fig_cand, ax_cand = plt.subplots(figsize=(10, 5))
    msno.matrix(candidates, ax=ax_cand, sparkline=False)
    st.pyplot(fig_cand)
    plt.close(fig_cand)

    st.caption("Fréquence des valeurs présentes par colonne.")
    fig_cand_bar, ax_cand_bar = plt.subplots(figsize=(10, 3))
    msno.bar(candidates, ax=ax_cand_bar, sort="descending")
    st.pyplot(fig_cand_bar)
    plt.close(fig_cand_bar)


## corr
st.subheader(t["quality_correlation_title"])
st.caption(t["quality_correlation_caption"])

tab_corr_dept, tab_corr_cand = st.tabs([
    "Départements",
    "Candidats",
])

with tab_corr_dept:
    dept_corr = numeric_correlation_matrix(
        departments,
        exclude={"code"},
    )
    if dept_corr.empty:
        st.info("Aucune colonne numérique exploitable dans le tableau départemental.")
    else:
        st.plotly_chart(
            plot_correlation_matrix(
                dept_corr,
                "Corrélations — indicateurs départementaux",
            ),
        )
        st.caption(
            "Une forte corrélation positive entre inscrits, votants et suffrages "
            "exprimés est attendue : ces variables décrivent des volumes liés."
        )
with tab_corr_cand:
    cand_corr = numeric_correlation_matrix(
        candidates,
        exclude={"code"},
    )
    if cand_corr.empty:
        st.info("Aucune colonne numérique exploitable dans le tableau des candidats.")
    else:
        st.plotly_chart(
            plot_correlation_matrix(
                cand_corr,
                "Corrélations — résultats candidats",
            ),
        )
        st.caption(
            "Les corrélations entre voix, pourcentages et rangs doivent être "
            "interprétées avec prudence : elles dépendent du format exact des "
            "colonnes produites par le parseur."
        )


# controls
st.subheader(t["quality_business_checks_title"])

consistency_checks, vote_check = election_consistency_checks(
    departments,
    candidates,
)

for check in consistency_checks:
    if check["passed"]:
        st.success(f"**{check['label']}** — {check['detail']}")
    else:
        st.warning(f"**{check['label']}** — {check['detail']}")

with st.expander("Détail : écart entre somme des voix candidates et suffrages exprimés"):
    st.dataframe(
        vote_check[
            ["code", "department", "valid", "candidate_votes_total", "vote_gap"]
        ]
        .sort_values("vote_gap", key=abs, ascending=False)
        .head(30),
        use_container_width=True,
        hide_index=True,
    )
    st.caption(
        "Un écart de 0 ou 1 voix peut provenir d’un arrondi dans le fichier source. "
        "Un écart important signale en revanche une anomalie potentielle."
    )


# dist et extreme vals
st.subheader(t["quality_distribution_title"])

departments["turnout_pct"] = 100 * departments["voters"].div(
    departments["registered"].replace(0, np.nan)
)

tab_turnout, tab_votes = st.tabs([
    "Participation",
    "Voix par candidat",
])
with tab_turnout:
    fig_turnout = px.histogram(
        departments,
        x="turnout_pct",
        nbins=30,
        title="Distribution de la participation départementale",
        labels={"turnout_pct": "Participation (%)", "count": "Nombre de départements"},
    )
    fig_turnout.update_layout(height=450)
    st.plotly_chart(fig_turnout, use_container_width=True)

    st.caption(
        "Les territoires d’outre-mer et les Français établis hors de France peuvent "
        "présenter des participations très différentes de celles de la métropole."
    )
with tab_votes:
    fig_votes = px.box(
        candidates,
        x="candidate",
        y="votes",
        points="outliers",
        title="Distribution des voix par candidat",
        labels={"candidate": "Candidat", "votes": "Voix"},
    )
    fig_votes.update_layout(height=550, xaxis_tickangle=-45)
    st.plotly_chart(fig_votes, use_container_width=True)

    st.caption(
        "Les valeurs élevées ne sont pas nécessairement des anomalies : elles "
        "reflètent la taille très différente des départements et territoires."
    )



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
