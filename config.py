"""Shared rules used by the cleaning script and the dashboard."""

# ---- Drugs -----------------------------------------------------------------
# (clean drug name, regex that matches any way it appears in a trial record).
# Brand names and lab codes are included so "Wegovy" and "LY3437943" are grouped
# with the right drug. Matching ignores upper/lower case.
DRUG_PATTERNS = [
    ("Semaglutide", r"semaglutide|semaglutin|wegovy|ozempic|rybelsus"),
    ("Tirzepatide", r"tirzepatide|mounjaro|zepbound|ly3298176"),
    ("Liraglutide", r"liraglutide|saxenda|victoza"),
    ("Dulaglutide", r"dulaglutide|trulicity|ly2189265"),
    ("Exenatide", r"exenatide|byetta|bydureon"),
    ("Retatrutide", r"retatrutide|ly3437943"),
    ("Survodutide", r"survodutide|bi ?456906"),
    ("Orforglipron", r"orforglipron|ly3502970"),
    ("CagriSema / cagrilintide", r"cagrisema|cagrilintide"),
]

# Used only when no named drug above is found (e.g. "GLP-1 receptor agonist").
OTHER_GLP1_PATTERN = (
    r"benaglutide|beinaglutide|zovaglutide|mazdutide|ecnoglutide|efpeglenatide|exendin-4|sar425899"
    r"|glp-?1|glucagon-like peptide|incretin"
)
# Names containing these words are NOT GLP-1 drugs (e.g. imaging tracers, blockers).
OTHER_GLP1_EXCLUDE = r"antagonist|tracer"
OTHER_DRUG_LABEL = "Other / unspecified GLP-1"

# ---- Sponsors --------------------------------------------------------------
# (regex on the lower-cased raw name, clean name). First match wins.
SPONSOR_ALIASES = [
    (r"novo nordisk", "Novo Nordisk"),
    (r"eli lilly|^lilly", "Eli Lilly"),
    (r"boehringer", "Boehringer Ingelheim"),
    (r"^pfizer", "Pfizer"),
    (r"astrazeneca", "AstraZeneca"),
    (r"glaxosmithkline|^gsk\b", "GlaxoSmithKline"),
    (r"innovent", "Innovent Biologics"),
    (r"hengrui", "Jiangsu HengRui Medicine"),
    (r"amsterdam umc", "Amsterdam UMC"),
    (r"mayo clinic", "Mayo Clinic"),
    (r"cleveland clinic", "Cleveland Clinic"),
    (r"university of colorado", "University of Colorado"),
    (r"mass(achusetts)? general", "Massachusetts General Hospital"),
    (r"zealand pharma", "Zealand Pharma"),
    (r"hanmi", "Hanmi Pharmaceutical"),
    (r"^sanofi", "Sanofi"),
    (r"hoffmann|^roche|^genentech", "Roche"),
    (r"^amgen", "Amgen"),
    (r"gan (&|and) lee", "Gan & Lee Pharmaceuticals"),
    (r"sciwind", "Sciwind Biosciences"),
    (r"chinese academy of sciences", "Chinese Academy of Sciences"),
]

# ---- Status / phase labels -------------------------------------------------
STATUS_LABELS = {
    "COMPLETED": "Completed",
    "RECRUITING": "Recruiting",
    "NOT_YET_RECRUITING": "Not yet recruiting",
    "ACTIVE_NOT_RECRUITING": "Active, not recruiting",
    "ENROLLING_BY_INVITATION": "Enrolling by invitation",
    "UNKNOWN": "Unknown",
    "WITHDRAWN": "Withdrawn",
    "TERMINATED": "Terminated",
    "SUSPENDED": "Suspended",
    "AVAILABLE": "Available",
}

PHASE_LABELS = {
    "EARLY_PHASE1": "Early Phase 1",
    "PHASE1": "Phase 1",
    "PHASE1 | PHASE2": "Phase 1/2",
    "PHASE2": "Phase 2",
    "PHASE2 | PHASE3": "Phase 2/3",
    "PHASE3": "Phase 3",
    "PHASE4": "Phase 4",
    "NA": "Not applicable",
}
PHASE_ORDER = ["Early Phase 1", "Phase 1", "Phase 1/2", "Phase 2", "Phase 2/3",
               "Phase 3", "Phase 4", "Not applicable"]

# ---- Countries -------------------------------------------------------------
# Two names are tidied before counting: ClinicalTrials.gov lists the old
# "Serbia and Montenegro" separately from Serbia, and writes "Turkey (Türkiye)".
COUNTRY_RENAMES = {
    "Serbia and Montenegro": "Serbia",
    "Turkey (Türkiye)": "Turkey",
}

# ISO-3 codes, which Plotly needs to colour countries on the world map.
COUNTRY_ISO3 = {
    "Algeria": "DZA", "Argentina": "ARG", "Australia": "AUS", "Austria": "AUT",
    "Bangladesh": "BGD", "Belgium": "BEL", "Brazil": "BRA", "Bulgaria": "BGR",
    "Cameroon": "CMR", "Canada": "CAN", "China": "CHN", "Colombia": "COL",
    "Croatia": "HRV", "Czechia": "CZE", "Denmark": "DNK", "Egypt": "EGY",
    "Finland": "FIN", "France": "FRA", "Georgia": "GEO", "Germany": "DEU",
    "Greece": "GRC", "Hong Kong": "HKG", "Hungary": "HUN", "India": "IND",
    "Iran": "IRN", "Ireland": "IRL", "Israel": "ISR", "Italy": "ITA",
    "Japan": "JPN", "Kazakhstan": "KAZ", "Kuwait": "KWT", "Latvia": "LVA",
    "Lebanon": "LBN", "Malaysia": "MYS", "Mexico": "MEX", "Netherlands": "NLD",
    "New Zealand": "NZL", "Norway": "NOR", "Pakistan": "PAK", "Paraguay": "PRY",
    "Poland": "POL", "Portugal": "PRT", "Puerto Rico": "PRI", "Romania": "ROU",
    "Russia": "RUS", "Saudi Arabia": "SAU", "Serbia": "SRB", "Singapore": "SGP",
    "Slovakia": "SVK", "Slovenia": "SVN", "South Africa": "ZAF",
    "South Korea": "KOR", "Spain": "ESP", "Sweden": "SWE", "Switzerland": "CHE",
    "Taiwan": "TWN", "Thailand": "THA", "Turkey": "TUR", "Ukraine": "UKR",
    "United Arab Emirates": "ARE", "United Kingdom": "GBR", "United States": "USA",
}
