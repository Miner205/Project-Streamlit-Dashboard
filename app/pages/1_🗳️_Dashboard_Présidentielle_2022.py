import logging
import pandas as pd
import plotly.express as px
import streamlit as st
from language_detection import detect_browser_language
from utils.i18n import load_content, normalize_language
from utils.parser import parse_results


SOURCE = "https://www.data.gouv.fr/datasets/election-presidentielle-des-10-et-24-avril-2022-resultats-definitifs-du-1er-tour"
st.set_page_config(page_title="Dashboard Présidentielle 2022", page_icon="🗳️", layout="wide")

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



with st.sidebar:
    page=st.radio("Navigation", range(len(t["pages"])), format_func=lambda i: t["pages"][i])
    uploaded=st.file_uploader(t["upload"],type=["txt","csv"])
    st.markdown(f'[{t["source"]}]({SOURCE})')




st.title(t["dashboard_title"])
st.markdown(f":small[Source: Election présidentielle des 10 et 24 avril 2022 - Résultats définitifs du 1er tour - par département — [{t["source"]}](https://www.data.gouv.fr/datasets/election-presidentielle-des-10-et-24-avril-2022-resultats-definitifs-du-1er-tour) — License Not Specifie]")



@st.cache_data(show_spinner=False)
def load_results(raw):
    departments, candidates, report = parse_results(raw)
    return pd.DataFrame(departments), pd.DataFrame(candidates), report


if page==0:
    st.subheader(t["home_title"])
    st.write(t["intro"])
    st.info(t["status"])
    st.stop()
if page==1:
    st.title(t["story_title"])
    st.write(t["question"])
    st.write(t["audience"])
    for item in t["story"]:
        st.markdown(f"- {item}")
    st.markdown(f'[{t["source"]}]({SOURCE})')
    st.warning(t["license"])
    st.info(t["geo"])
    st.stop()
if uploaded is None:
    st.info(t["waiting"])
    st.stop()
try:
    departments,candidates,report = load_results(uploaded.getvalue())
except ValueError as exc:
    st.error(f'{t["error"]}: {exc}')
    st.stop()

if page==4:
    st.title(t["quality_title"])
    st.write(t["quality_intro"])
    a,b,c=st.columns(3)
    a.metric(t["rows"],len(departments))
    b.metric(t["encoding"],report["encoding"])
    missing=int(departments.isna().sum().sum()+candidates.isna().sum().sum())
    c.metric(t["missing"],missing)
    for item in t["quality_checks"]:
        st.markdown(f"- {item}")
    if report["issues"]:
        st.warning(t["quality_bad"])
        with st.expander(t["quality_details"],expanded=True):
            for issue in report["issues"]:
                st.write(issue)
    else:
        st.success(t["quality_ok"])
    st.warning(t["license"])
    st.info(t["geo"])
    st.write(t["conclusions"])
    st.stop()

with st.sidebar:
    st.header(t["filters"])
    codes=st.multiselect(t["departments"],departments["code"].tolist(),default=departments["code"].tolist(),format_func=lambda code:code+" · "+departments.set_index("code").loc[code,"department"])
    names=sorted(candidates["candidate"].unique())
    chosen=st.multiselect(t["candidates"],names,default=names)
if not codes or not chosen:
    st.warning(t["empty"])
    st.stop()
d=departments[departments["code"].isin(codes)].copy()
all_c=candidates[candidates["code"].isin(codes)].copy()
c=all_c[all_c["candidate"].isin(chosen)].copy()
registered=int(d["registered"].sum())
voters=int(d["voters"].sum())
valid=int(d["valid"].sum())
st.title(t["eda_title"] if page==2 else t["analysis_title"])
st.caption(t["selected"])
if report["issues"]:
    st.warning(t["quality_bad"])
for col,label,value in zip(st.columns(3),t["kpis"],[f"{registered:,}",f"{100*voters/registered:.2f} %" if registered else "—",f"{valid:,}"]):
    col.metric(label,value)
# Candidate filtering never changes turnout or the valid-vote denominator.
st.caption("Le filtre candidat ne change pas la participation ni le dénominateur des scores." if lang=="fr" else "Candidate selection does not change turnout or vote-share denominators.")
d["turnout_pct"]=100*d["voters"].div(d["registered"].replace(0,float("nan")))
if page==2:
    st.subheader(t["tables"][0])
    st.dataframe(d,use_container_width=True,hide_index=True)
    st.subheader(t["tables"][1])
    st.dataframe(c,use_container_width=True,hide_index=True)
else:
    labels={"department":t["department"],"candidate":t["candidate"],"votes":t["votes"],"turnout_pct":t["turnout"],"share":t["score"]}
    st.subheader(t["charts"][0])
    st.plotly_chart(px.bar(d.sort_values("turnout_pct"),x="turnout_pct",y="department",orientation="h",labels=labels,height=max(450,22*len(d))),use_container_width=True)
    agg=c.groupby("candidate",as_index=False)["votes"].sum()
    agg["share"]=100*agg["votes"]/valid if valid else float("nan")
    st.subheader(t["charts"][1])
    st.plotly_chart(px.bar(agg.sort_values("share"),x="share",y="candidate",orientation="h",hover_data=["votes"],labels=labels),use_container_width=True)
    joined=c.merge(d[["code","valid"]],on="code",validate="many_to_one")
    joined["share"]=100*joined["votes"].div(joined["valid"].replace(0,float("nan")))
    st.subheader(t["charts"][2])
    matrix=joined.pivot(index="department",columns="candidate",values="share")
    fig=px.imshow(matrix,aspect="auto",color_continuous_scale="Blues",labels={"x":t["candidate"],"y":t["department"],"color":t["score"]},height=max(450,22*len(d)))
    fig.update_traces(hovertemplate="%{y}<br>%{x}<br>%{z:.2f} %<extra></extra>")
    st.plotly_chart(fig,use_container_width=True)
    st.info(t["geo"])
    st.write(t["conclusions"])
