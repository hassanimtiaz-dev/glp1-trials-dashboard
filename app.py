"""GLP-1 obesity clinical trials dashboard (Streamlit + Plotly).

Run locally:  streamlit run app.py
Reads the cleaned file data/glp1_trials_clean.csv, so it never calls the API.
"""
import html
from datetime import date
from pathlib import Path

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

import config

DATA_DIR = Path(__file__).parent / "data"

# ---- Colours ---------------------------------------------------------------
# One blue shade for "how many" charts; each drug keeps its own colour everywhere,
# so Semaglutide is always blue even if other drugs are filtered out.
BLUE, BLUE_LIGHT, BLUE_DARK = "#2a78d6", "#86b6ef", "#0d366b"
INK, MUTED, GRID = "#1a1a19", "#52514e", "#e6e5e0"
DRUG_COLORS = {
    "Semaglutide": "#2a78d6",
    "Tirzepatide": "#eb6834",
    "Liraglutide": "#1baf7a",
    "Exenatide": "#eda100",
    "CagriSema / cagrilintide": "#e87ba4",
    "Orforglipron": "#008300",
    "Survodutide": "#4a3aa7",
    "Retatrutide": "#e34948",
    "Dulaglutide": "#8a8984",
}
DEFAULT_COMPARE = ["Semaglutide", "Tirzepatide", "Liraglutide"]
BIG_STUDY = 50_000  # trials above this size are real-world database studies

st.set_page_config(page_title="GLP-1 Obesity Trials Dashboard", page_icon="📊", layout="wide")

st.markdown(
    """
    <style>
      .block-container {padding-top: 2.2rem; max-width: 1280px;}
      h1 {font-size: 2.1rem !important; margin-bottom: 0.2rem;}
      .subtitle {color: #52514e; font-size: 1.02rem; margin-bottom: 1.2rem;}
      .insight {border: 1px solid #e6e5e0; border-radius: 10px; padding: 16px 18px;
                background: #fbfbfa; min-height: 205px;}
      .insight .label {font-size: 0.78rem; text-transform: uppercase; letter-spacing: .05em;
                       color: #52514e; font-weight: 600;}
      .insight .big {font-size: 2rem; font-weight: 700; color: #184f95; line-height: 1.2;
                     margin: 4px 0 6px 0;}
      .insight .text {font-size: 0.93rem; color: #1a1a19; line-height: 1.4;}
    </style>
    """,
    unsafe_allow_html=True,
)


# ---- Load data -------------------------------------------------------------
@st.cache_data
def load_data():
    """Read the cleaned CSV once and add list versions of the 'a | b' columns."""
    df = pd.read_csv(DATA_DIR / "glp1_trials_clean.csv", parse_dates=["start_date", "completion_date"])
    df["start_year"] = df["start_year"].astype("Int64")
    df["countries"] = df["countries"].fillna("")
    df["drug_list"] = df["drugs"].str.split(" | ", regex=False)
    df["country_list"] = df["countries"].map(lambda s: s.split(" | ") if s else [])
    snapshot = date.fromisoformat((DATA_DIR / "snapshot_date.txt").read_text().strip())
    return df, snapshot


df, snapshot = load_data()

# ---- Sidebar filters -------------------------------------------------------
st.sidebar.header("Filters")
st.sidebar.caption("Leave a box empty to include everything.")

all_drugs = sorted({d for lst in df["drug_list"] for d in lst},
                   key=lambda d: (d == config.OTHER_DRUG_LABEL, d))
sel_drugs = st.sidebar.multiselect("Drug", all_drugs, placeholder="All drugs")

phases_present = [p for p in config.PHASE_ORDER if p in set(df["phase"])]
sel_phases = st.sidebar.multiselect("Phase", phases_present, placeholder="All phases")

sponsors_by_count = df["sponsor"].value_counts().index.tolist()
sel_sponsors = st.sidebar.multiselect("Sponsor", sponsors_by_count, placeholder="All sponsors")

min_year, max_year = int(df["start_year"].min()), int(df["start_year"].max())
year_range = st.sidebar.slider("Start year", min_year, max_year, (min_year, max_year))

mask = pd.Series(True, index=df.index)
if sel_drugs:
    mask &= df["drug_list"].map(lambda drugs: any(d in sel_drugs for d in drugs))
if sel_phases:
    mask &= df["phase"].isin(sel_phases)
if sel_sponsors:
    mask &= df["sponsor"].isin(sel_sponsors)
in_years = df["start_year"].between(*year_range).fillna(False).astype(bool)
no_start_year = df["start_year"].isna() & (year_range == (min_year, max_year))
mask &= in_years | no_start_year
f = df[mask]

st.sidebar.markdown("---")
st.sidebar.caption(f"Showing **{len(f):,}** of {len(df):,} trials")

# ---- Header ----------------------------------------------------------------
st.title("GLP-1 Obesity Drug Trials")
st.markdown(
    "<div class='subtitle'>Clinical trials of semaglutide, tirzepatide, liraglutide and other "
    "GLP-1-based drugs in obesity and weight management, from ClinicalTrials.gov "
    f"· data snapshot {snapshot:%d %b %Y}</div>",
    unsafe_allow_html=True,
)

if f.empty:
    st.warning("No trials match these filters. Try removing a filter.")
    st.stop()

# ---- Headline numbers ------------------------------------------------------
countries_in_f = {c for lst in f["country_list"] for c in lst}
c1, c2, c3, c4 = st.columns(4)
c1.metric("Total trials", f"{len(f):,}", border=True)
total_people = int(f["enrolment"].sum())
c2.metric("Total participants", f"{total_people / 1e6:.2f}M" if total_people >= 1_000_000 else f"{total_people:,}",
          border=True)
c3.metric("Sponsors", f"{f['sponsor'].nunique():,}", border=True)
c4.metric("Countries", f"{len(countries_in_f):,}", border=True)

big = f[f["enrolment"] > BIG_STUDY]
if len(big):
    share = big["enrolment"].sum() / f["enrolment"].sum()
    st.caption(
        f"Participants include {len(big)} very large real-world database "
        f"{'study' if len(big) == 1 else 'studies'} (over {BIG_STUDY:,} people each), "
        f"which make up {share:.0%} of the total. Planned (not yet final) enrolment is counted for ongoing trials."
    )


# ---- Chart helpers ---------------------------------------------------------
def show(fig, height=340, legend=False):
    """Apply the shared look to a Plotly figure and draw it."""
    fig.update_layout(
        height=height, margin=dict(l=0, r=10, t=10, b=0), showlegend=legend,
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="sans-serif", size=13, color=INK),
        hoverlabel=dict(bgcolor="white", font_size=13, font_color=INK),
        barcornerradius=3, dragmode=False,  # charts are read-only: no accidental drag or zoom
    )
    fig.update_xaxes(automargin=True)  # make room for axis labels
    fig.update_yaxes(automargin=True)
    st.plotly_chart(fig, width="stretch", theme=None, config={"displayModeBar": False, "scrollZoom": False})


def card_title(title, note=None):
    st.markdown(f"**{title}**")
    if note:
        st.caption(note)


def hbar(labels, values, hover_names=None):
    """Horizontal bar chart in a single blue, biggest value at the top."""
    fig = go.Figure(go.Bar(
        x=values, y=labels, orientation="h", marker_color=BLUE,
        text=values, textposition="outside", cliponaxis=False,
        customdata=hover_names if hover_names is not None else labels,
        hovertemplate="<b>%{customdata}</b><br>%{x} trials<extra></extra>",
    ))
    fig.update_yaxes(autorange="reversed", showgrid=False, linecolor=GRID, ticksuffix="  ",
                     automargin=True)  # automargin makes room for long labels
    fig.update_xaxes(showgrid=True, gridcolor=GRID, zeroline=False, showticklabels=False,
                     range=[0, max(values) * 1.15])  # leave room for the number at the bar end
    fig.update_layout(bargap=0.35)
    return fig


dated = f.dropna(subset=["start_year"])
years = range(int(dated["start_year"].min()), int(dated["start_year"].max()) + 1) if len(dated) else range(0)

# ---- Row 1: trials per year | trials by phase ------------------------------
left, right = st.columns([3, 2])
with left, st.container(border=True):
    card_title("Trials started per year",
               f"Lighter bars: {snapshot.year} is still in progress and later years are planned start dates.")
    per_year = dated.groupby("start_year").size().reindex(years, fill_value=0)
    fig = go.Figure(go.Bar(
        x=list(per_year.index), y=per_year.values,
        marker_color=[BLUE_LIGHT if y >= snapshot.year else BLUE for y in per_year.index],
        hovertemplate="<b>%{x}</b><br>%{y} trials started<extra></extra>",
    ))
    fig.update_xaxes(dtick=2, showgrid=False, linecolor=GRID)
    fig.update_yaxes(showgrid=True, gridcolor=GRID, zeroline=False)
    fig.update_layout(bargap=0.25)
    show(fig)

with right, st.container(border=True):
    card_title("Trials by phase", "'Not applicable' covers behavioural and observational studies.")
    by_phase = f["phase"].value_counts().reindex(config.PHASE_ORDER).dropna().astype(int)
    show(hbar(by_phase.index.tolist(), by_phase.values), height=340)

# ---- Row 2: top sponsors | trial status ------------------------------------
left, right = st.columns(2)
with left, st.container(border=True):
    card_title("Top 10 sponsors", "The organisation leading each trial.")
    top = f["sponsor"].value_counts().head(10)
    short = [s if len(s) <= 34 else s[:33] + "…" for s in top.index]
    show(hbar(short, top.values, hover_names=top.index.tolist()), height=380)

with right, st.container(border=True):
    card_title("Trial status", "Where each trial is now.")
    by_status = f["status"].value_counts()
    show(hbar(by_status.index.tolist(), by_status.values), height=380)

# ---- Row 3: drugs over time ------------------------------------------------
with st.container(border=True):
    card_title("Trials started per year, by drug",
               f"Complete years only (to {snapshot.year - 1}); {snapshot.year} is still in progress. "
               "A trial testing two drugs counts once for each. Pick drugs to compare.")
    compare = st.multiselect("Drugs to compare", list(DRUG_COLORS), default=DEFAULT_COMPARE,
                             label_visibility="collapsed")
    full_years = range(int(dated["start_year"].min()), snapshot.year) if len(dated) else range(0)
    ex = dated[dated["start_year"] < snapshot.year].explode("drug_list")
    ex = ex[ex["drug_list"].isin(compare)]
    if ex.empty or not compare:
        st.info("Choose at least one drug with trials in the current filters.")
    else:
        table = ex.groupby(["start_year", "drug_list"]).size().unstack(fill_value=0).reindex(full_years, fill_value=0)
        fig = go.Figure()
        for drug in compare:  # loop in the order the user picked; colours stay fixed per drug
            if drug in table.columns:
                fig.add_trace(go.Scatter(
                    x=list(table.index), y=table[drug].values, name=drug, mode="lines+markers",
                    line=dict(color=DRUG_COLORS[drug], width=2.5),
                    marker=dict(size=7, color=DRUG_COLORS[drug], line=dict(color="white", width=1.5)),
                    hovertemplate="%{y} trials<extra>" + drug + "</extra>",
                ))
        fig.update_xaxes(dtick=2, showgrid=False, linecolor=GRID)
        fig.update_yaxes(showgrid=True, gridcolor=GRID, zeroline=False, rangemode="tozero")
        fig.update_layout(hovermode="x unified", legend=dict(orientation="h", y=1.12, x=0))
        show(fig, height=380, legend=True)

# ---- Row 4: world map ------------------------------------------------------
with st.container(border=True):
    card_title("Where the trials run",
               "Number of trials with at least one site in each country (colour scale is logarithmic). "
               "Trials with no listed sites are not shown.")
    located = f.explode("country_list").dropna(subset=["country_list"])
    per_country = located.groupby("country_list")["nct_id"].nunique().reset_index(name="trials")
    per_country["iso3"] = per_country["country_list"].map(config.COUNTRY_ISO3)
    per_country = per_country.dropna(subset=["iso3"])
    if per_country.empty:
        st.info("No country information for the selected trials.")
    else:
        top_n = int(per_country["trials"].max())
        ticks = [t for t in (1, 3, 10, 30, 100, 300, 1000) if t <= top_n * 1.5]
        fig = go.Figure(go.Choropleth(
            locations=per_country["iso3"], z=np.log10(per_country["trials"]),
            text=per_country["country_list"], customdata=per_country["trials"],
            hovertemplate="<b>%{text}</b><br>%{customdata} trials<extra></extra>",
            colorscale=[[0, "#cde2fb"], [0.5, "#3987e5"], [1, BLUE_DARK]], zmin=0,
            marker_line_color="white", marker_line_width=0.5,
            colorbar=dict(title="Trials", tickvals=np.log10(ticks), ticktext=[str(t) for t in ticks],
                          thickness=12, len=0.6),
        ))
        fig.update_geos(projection_type="natural earth", showframe=False, showcoastlines=False,
                        showcountries=True, countrycolor="white", landcolor="#eceae5",
                        showocean=False, bgcolor="rgba(0,0,0,0)",
                        center=dict(lat=14, lon=8), projection_scale=1.15)
        show(fig, height=480)


# ---- Key insights (all calculated from the filtered data) ------------------
def build_insights(data, last_full_year):
    """Return four (label, big number, sentence) tuples worked out from `data`."""
    insights = []

    # 1. Growth in trials started per year since 2020
    by_year = data.groupby("start_year").size()
    start, latest = int(by_year.get(2020, 0)), int(by_year.get(last_full_year, 0))
    if start > 0 and latest > 0:
        insights.append(("Growth since 2020", f"{(latest - start) / start:+.0%}",
                         f"Trials starting each year went from {start} in 2020 to {latest} in "
                         f"{last_full_year}, the last full year."))
    else:
        insights.append(("Growth since 2020", "n/a",
                         f"Needs trials starting in both 2020 and {last_full_year}: widen the filters."))

    # 2. Share held by the top two sponsors
    top2 = data["sponsor"].value_counts().head(2)
    share = top2.sum() / len(data)
    names = " and ".join(top2.index)
    insights.append(("Concentration", f"{share:.0%}",
                     f"{names} {'sponsor' if len(top2) > 1 else 'sponsors'} {top2.sum()} of the "
                     f"{len(data)} trials shown."))

    # 3. Typical (median) trial size by phase
    sizes = data.groupby("phase")["enrolment"].median().reindex(["Phase 1", "Phase 2", "Phase 3"]).dropna()
    if len(sizes) >= 2:
        parts = ", ".join(f"{int(v):,} in {p}" for p, v in sizes.items())
        insights.append(("Trial size by phase", f"{int(sizes.iloc[-1]):,}",
                         f"Median enrolment is {parts} (median used so a few huge studies "
                         f"don't skew it)."))
    else:
        insights.append(("Trial size by phase", "n/a", "Needs trials from at least two phases."))

    # 4. Which drug's share of new trials has risen most
    cutoff = last_full_year - 2
    dated_data = data.dropna(subset=["start_year"])
    recent, earlier = dated_data[dated_data["start_year"] >= cutoff], dated_data[dated_data["start_year"] < cutoff]
    best = None
    if len(recent) >= 10 and len(earlier) >= 10:
        for drug in DRUG_COLORS:
            now = recent["drug_list"].map(lambda l: drug in l).mean()
            before = earlier["drug_list"].map(lambda l: drug in l).mean()
            if recent["drug_list"].map(lambda l: drug in l).sum() >= 5 and (best is None or now - before > best[1] - best[2]):
                best = (drug, now, before)
    if best and best[1] > best[2]:
        insights.append(("Fastest-rising drug", best[0].split(" /")[0],
                         f"{best[0]} appears in {best[1]:.0%} of trials started since {cutoff}, "
                         f"up from {best[2]:.0%} of those started before."))
    else:
        top_drug = data.explode("drug_list")["drug_list"].value_counts().index[0]
        insights.append(("Most-studied drug", top_drug.split(" /")[0],
                         f"{top_drug} features in {data['drug_list'].map(lambda l: top_drug in l).mean():.0%} "
                         f"of the trials shown."))
    return insights


st.markdown("### Key insights")
st.caption("Recalculated from the trials currently selected by the filters.")
cols = st.columns(4)
for col, (label, big_number, text) in zip(cols, build_insights(f, snapshot.year - 1)):
    col.markdown(
        f"<div class='insight'><div class='label'>{html.escape(label)}</div>"
        f"<div class='big'>{html.escape(big_number)}</div>"
        f"<div class='text'>{html.escape(text)}</div></div>",
        unsafe_allow_html=True,
    )

# ---- Searchable table ------------------------------------------------------
st.markdown("### Trial explorer")
query = st.text_input("Search trials", placeholder="Search by title, drug, sponsor, country or NCT number…",
                      label_visibility="collapsed")
table = f
if query:
    haystack = (f["nct_id"] + " " + f["title"] + " " + f["drugs"] + " " + f["sponsor"] + " " + f["countries"])
    table = f[haystack.str.contains(query, case=False, regex=False)]
st.caption(f"Showing {len(table):,} of {len(f):,} trials. Click a column heading to sort; click an ID to open the trial.")

view = table.sort_values("start_date", ascending=False).assign(
    start=lambda d: d["start_date"].dt.strftime("%Y-%m").fillna(""))
st.dataframe(
    view[["url", "title", "drugs", "sponsor", "phase", "status", "start", "enrolment", "countries"]],
    hide_index=True, width="stretch", height=480,
    column_config={
        "url": st.column_config.LinkColumn("Trial ID", display_text=r"study/(NCT\d+)", width="small"),
        "title": st.column_config.TextColumn("Title", width="large"),
        "drugs": st.column_config.TextColumn("Drug(s)"),
        "sponsor": st.column_config.TextColumn("Sponsor"),
        "phase": st.column_config.TextColumn("Phase", width="small"),
        "status": st.column_config.TextColumn("Status"),
        "start": st.column_config.TextColumn("Start", width="small"),
        "enrolment": st.column_config.NumberColumn("Enrolment", format="%d"),
        "countries": st.column_config.TextColumn("Countries"),
    },
)

st.caption(
    "Source: ClinicalTrials.gov API v2. Trials were selected by obesity/weight-management condition and a "
    "GLP-1-based drug in the interventions or title. Registered trials only: not every study is published or completed."
)
