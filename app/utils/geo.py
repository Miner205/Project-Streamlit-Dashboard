from pathlib import Path
import geopandas as gpd
import plotly.express as px
import streamlit as st


GEO_PATH = Path("data/departements-20180101-shp/departements-20180101.shp")
GEO_SOURCE = "https://www.data.gouv.fr/datasets/contours-des-departements-francais-issus-d-openstreetmap"
GEO_ATTRIBUTION = "© les contributeurs d’OpenStreetMap sous licence ODbL"

# Codes utilisés dans le dataset présidentiel 2022.
# Certains territoires ne possèdent pas de département dans le shapefile OSM.
ELECTION_TO_INSEE = {
    "ZA": "971",  # Guadeloupe
    "ZB": "972",  # Martinique
    "ZC": "973",  # Guyane
    "ZD": "974",  # La Réunion
    "ZM": "976",  # Mayotte
}
# Territoires présents dans les résultats mais sans polygone départemental OSM.
NON_CARTOGRAPHIABLE = {
    "ZN": "Nouvelle-Calédonie",
    "ZP": "Polynésie française",
    "ZS": "Saint-Pierre-et-Miquelon",
    "ZW": "Wallis-et-Futuna",
    "ZX": "Saint-Martin / Saint-Barthélemy",
    "ZZ": "Français établis hors de France",
}

TERRITORIES = {
    "Toutes circonscriptions": None,
    "France métropolitaine": [
        "01", "02", "03", "04", "05", "06", "07", "08", "09", "10",
        "11", "12", "13", "14", "15", "16", "17", "18", "19", "2A", "2B",
        "21", "22", "23", "24", "25", "26", "27", "28", "29", "30", "31",
        "32", "33", "34", "35", "36", "37", "38", "39", "40", "41", "42",
        "43", "44", "45", "46", "47", "48", "49", "50", "51", "52", "53",
        "54", "55", "56", "57", "58", "59", "60", "61", "62", "63", "64",
        "65", "66", "67", "68", "69", "70", "71", "72", "73", "74", "75",
        "76", "77", "78", "79", "80", "81", "82", "83", "84", "85", "86",
        "87", "88", "89", "90", "91", "92", "93", "94", "95",
    ],
    "Corse": ["2A", "2B"],
    "Outre-mer cartographiable": ["ZA", "ZB", "ZC", "ZD", "ZM"],
    "Guadeloupe": ["ZA"],
    "Martinique": ["ZB"],
    "Guyane": ["ZC"],
    "La Réunion": ["ZD"],
    "Mayotte": ["ZM"],
    "Territoires non cartographiables": list(NON_CARTOGRAPHIABLE),
}


@st.cache_data(show_spinner="Chargement des contours départementaux…")
def load_departements_geo():
    if not GEO_PATH.exists():
        return None

    geo = gpd.read_file(GEO_PATH)

    # Normalisation des attributs OSM.
    geo = geo.rename(
        columns={
            "code_insee": "geo_code",
            "nom": "department",
            "surf_km2": "area_km2",
        }
    )

    required = {"geo_code", "department", "geometry"}
    if not required.issubset(geo.columns):
        raise ValueError(
            f"Attributs manquants dans le shapefile : {required - set(geo.columns)}"
        )

    #geo["geo_code"] = geo["geo_code"].astype(str).str.zfill(3)
    geo["geo_code"] = geo["geo_code"].map(normalize_department_code)
    geo["department"] = geo["department"].astype(str)
    # Évite les géométries invalides et allège les attributs inutiles.
    geo["geometry"] = geo.geometry.make_valid()
    keep = [
        col for col in ["geo_code", "department", "nuts3", "wikidata", "area_km2", "geometry"]
        if col in geo.columns
    ]
    return geo[keep].copy()


def normalize_election_codes(df):
    """Ajoute `geo_code` à un DataFrame électoral basé sur sa colonne `code`."""
    out = df.copy()
    #out["code"] = out["code"].astype(str).str.upper()
    out["code"] = out["code"].map(normalize_department_code)
    out["geo_code"] = out["code"].map(ELECTION_TO_INSEE)

    # Métropole et Corse : le code électoral est déjà le code INSEE.
    metropolitan_mask = ~out["code"].isin(ELECTION_TO_INSEE) & ~out["code"].isin(
        NON_CARTOGRAPHIABLE
    )
    out.loc[metropolitan_mask, "geo_code"] = out.loc[metropolitan_mask, "code"]

    return out

def normalize_department_code(value):
    """
    Normalise un code département :
    - supprime les espaces
    - met en majuscules
    - complète les codes numériques métropolitains sur deux caractères
    - préserve 2A, 2B et les codes outre-mer
    """
    code = str(value).strip().upper()

    if code in {"2A", "2B"}:
        return code

    if code.isdigit():
        return code.zfill(2)

    return code


def territory_filter(label="Territoire à afficher"):
    """Filtre persistant dans la sidebar, conservé entre les pages Streamlit."""
    if "territory" not in st.session_state:
        st.session_state["territory"] = "France métropolitaine"

    return st.selectbox(
        label,
        list(TERRITORIES.keys()),
        key="territory"
    )


def filter_by_territory(df, territory):
    """Filtre un DataFrame électoral selon son code département électoral."""
    codes = TERRITORIES.get(territory)
    if codes is None:
        return df.copy()
    return df[df["code"].astype(str).str.upper().isin(codes)].copy()


def department_map(t,
    geo,
    values,
    *,
    color_label,
    territory="France métropolitaine",
    color_scale="Blues",
    hover_data=None,
    center=None,
):
    """
    Construit une carte choroplèthe départementale.

    `values` doit être un DataFrame avec au minimum :
    - `code` : code département (code du dataset électoral (`01`, `2A`, `ZA`, etc.))
    - une colonne numérique à cartographier
    """
    if geo is None:
        st.warning(f"{t["map_missing_shapefile"]}")
        return None

    mapped = normalize_election_codes(values)
    mapped = mapped.dropna(subset=["geo_code"])

    map_df = geo.merge(
        mapped.drop(columns="code"),
        on="geo_code",
        how="inner",
        validate="one_to_one",
    )

    # Conversion du filtre électoral vers les codes INSEE du shapefile.
    election_to_insee = ELECTION_TO_INSEE
    selected_codes = TERRITORIES.get(territory)

    if selected_codes is not None:
        selected_geo_codes = {
            election_to_insee.get(code, code) for code in selected_codes
        }
        map_df = map_df[map_df["geo_code"].isin(selected_geo_codes)]

    if map_df.empty:
        st.warning(
            f"{t["map_no_data"]}"
            f"{t["map_missing_overseas"]}"
        )
        return None

    value_col = [col for col in mapped.columns if col not in {"code", "geo_code"}][-1]

    fig = px.choropleth_map(
        map_df,
        geojson=map_df.__geo_interface__,
        locations="geo_code",
        featureidkey="properties.geo_code",
        color=value_col,
        color_continuous_scale=color_scale,
        hover_name="department",
        hover_data=hover_data,
        labels={value_col: color_label, "department": "Département"},
        center=center or {"lat": 46.6, "lon": 2.4},
        zoom=4.1,
        opacity=0.82,
        height=620,
    )

    fig.update_layout(
        margin={"r": 0, "t": 0, "l": 0, "b": 0},
        coloraxis_colorbar={"title": color_label},
        map_style="carto-positron",
    )
    fig.update_traces(
        marker={"line": {"width": 0.4, "color": "white"}},
        hovertemplate="<b>%{customdata[0]}</b><br>"
        f"{color_label} : %{{z:.2f}}<extra></extra>",
        customdata=map_df[["department"]].values,
    )
    return fig


def show_geo_credit(t):
    st.caption(
        f"{t["geo_credit"][0]} [{t["geo_credit"][1]}]({GEO_SOURCE}) — "
        f"{GEO_ATTRIBUTION}. {t["geo_credit"][2]}"
    )
