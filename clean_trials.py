"""Stage 2: clean the raw trial data.

Run:  python3 clean_trials.py
Input:  data/raw_trials.csv
Output: data/glp1_trials_clean.csv  (the file the dashboard reads)
"""
import re

import pandas as pd

import config

RAW_FILE = "data/raw_trials.csv"
CLEAN_FILE = "data/glp1_trials_clean.csv"


def clean_sponsor(raw):
    """Merge name variants, e.g. 'Novo Nordisk A/S' -> 'Novo Nordisk'."""
    name = raw.strip()
    for pattern, clean_name in config.SPONSOR_ALIASES:
        if re.search(pattern, name.lower()):
            return clean_name
    name = re.sub(r"^the\s+", "", name, flags=re.I)  # "The Cleveland Clinic"
    # Drop company endings such as ", Inc." / " Ltd." / " A/S".
    name = re.sub(r",?\s+(inc\.?|ltd\.?|llc|gmbh|a/s|co\.,? ltd\.?|corporation|corp\.?|limited|pty\.?)$",
                  "", name, flags=re.I)
    return re.sub(r"\s+", " ", name).strip()


def find_drugs(interventions, title):
    """Return the clean drug names mentioned in a trial, e.g. 'Semaglutide | Tirzepatide'."""
    # Ignore names that clearly are not GLP-1 drugs (imaging tracers, antagonists).
    names = [n for n in ("" if pd.isna(interventions) else interventions).split(" | ")
             if not re.search(config.OTHER_GLP1_EXCLUDE, n, flags=re.I)]
    text = " | ".join(names)

    found = [drug for drug, pattern in config.DRUG_PATTERNS
             if re.search(pattern, text, flags=re.I)]
    if not found:  # interventions were empty or only gave a lab code: try the title
        found = [drug for drug, pattern in config.DRUG_PATTERNS
                 if re.search(pattern, title, flags=re.I)]
    if not found and re.search(config.OTHER_GLP1_PATTERN, text + " " + title, flags=re.I):
        found = [config.OTHER_DRUG_LABEL]
    return " | ".join(found)  # empty text means: no GLP-1 drug found


def clean_countries(raw):
    """Tidy country names and return them sorted, joined with ' | '."""
    if pd.isna(raw) or raw == "":
        return ""
    countries = {config.COUNTRY_RENAMES.get(c, c) for c in raw.split(" | ")}
    return " | ".join(sorted(countries))


def main():
    # keep_default_na=False stops pandas turning the phase value "NA" into "missing".
    df = pd.read_csv(RAW_FILE, keep_default_na=False, na_values=[""])
    rows_before = len(df)
    df = df.drop_duplicates(subset="nct_id").copy()

    df["sponsor_raw"] = df["sponsor"]
    df["sponsor"] = df["sponsor"].fillna("Unknown sponsor").map(clean_sponsor)
    # If two spellings differ only by capital letters, keep the most common spelling.
    most_common = df.groupby(df["sponsor"].str.lower())["sponsor"].agg(lambda s: s.value_counts().index[0])
    df["sponsor"] = df["sponsor"].str.lower().map(most_common)

    df["drugs"] = [find_drugs(i, t) for i, t in zip(df["interventions"], df["title"])]
    # The API also matches drug words buried in long descriptions (e.g. a diet or
    # surgery trial that only mentions GLP-1 in passing). Keep a trial only if a
    # GLP-1 drug or term appears in its interventions or title.
    not_glp1 = df["drugs"] == ""
    print(f"Dropped {not_glp1.sum()} trials with no GLP-1 drug in interventions/title")
    df = df[~not_glp1].copy()

    # A blank phase means the record has no phase (e.g. observational studies).
    df["phase"] = df["phase"].fillna("NA").map(config.PHASE_LABELS)
    df["status"] = df["status"].map(config.STATUS_LABELS).fillna("Unknown")

    # Dates come as 2024-03-18 or just 2024-03; unreadable/missing become blank.
    for col in ["start_date", "completion_date"]:
        df[col] = pd.to_datetime(df[col], format="mixed", errors="coerce")
    df["start_year"] = df["start_date"].dt.year.astype("Int64")

    df["enrolment"] = pd.to_numeric(df["enrolment"], errors="coerce")

    df["countries"] = df["countries"].map(clean_countries)
    df["n_countries"] = df["countries"].map(lambda s: len(s.split(" | ")) if s else 0)

    df["url"] = "https://clinicaltrials.gov/study/" + df["nct_id"]

    columns = ["nct_id", "title", "drugs", "sponsor", "phase", "status", "start_date",
               "completion_date", "start_year", "enrolment", "enrolment_type",
               "countries", "n_countries", "url", "sponsor_raw"]
    df[columns].to_csv(CLEAN_FILE, index=False)

    print(f"Rows in: {rows_before}   Rows out: {len(df)}")
    print(f"Sponsors: {df['sponsor_raw'].nunique()} raw names -> {df['sponsor'].nunique()} clean names")
    print("\nMissing values after cleaning:")
    print(df[columns].isna().sum()[lambda s: s > 0].to_string())
    print(f"(plus {(df['n_countries'] == 0).sum()} trials with no listed countries)")
    print(f"\nSaved {CLEAN_FILE}")


if __name__ == "__main__":
    main()
