"""Stage 1: download GLP-1 obesity trials from the ClinicalTrials.gov API v2.

Run:  python3 fetch_trials.py
Output: data/raw_trials.csv  (one row per trial, lists joined with " | ")
"""
import time
from datetime import date
from pathlib import Path

import pandas as pd
import requests

API_URL = "https://clinicaltrials.gov/api/v2/studies"

# Trials must list one of these conditions...
CONDITION_QUERY = 'obesity OR overweight OR "weight management"'

# ...AND involve one of these GLP-1-based drugs (the API also matches brand names).
DRUG_QUERY = (
    "semaglutide OR tirzepatide OR liraglutide OR dulaglutide OR exenatide "
    "OR retatrutide OR survodutide OR cagrilintide OR CagriSema OR orforglipron"
)

# Only ask the API for the fields we need (keeps the download small and fast).
FIELDS = "|".join([
    "NCTId", "BriefTitle", "LeadSponsorName", "Phase", "OverallStatus",
    "StartDate", "CompletionDate", "EnrollmentCount", "EnrollmentType",
    "InterventionName", "LocationCountry",
])

OUT_FILE = Path("data/raw_trials.csv")


def fetch_all_studies():
    """Request pages of up to 1000 trials until the API says there are no more."""
    studies, page_token = [], None
    while True:
        params = {
            "query.cond": CONDITION_QUERY,
            "query.intr": DRUG_QUERY,
            "fields": FIELDS,
            "pageSize": 1000,
            "countTotal": "true",
        }
        if page_token:
            params["pageToken"] = page_token

        response = requests.get(API_URL, params=params, timeout=60)
        response.raise_for_status()  # stop with a clear error if the API fails
        data = response.json()

        studies.extend(data["studies"])
        print(f"Downloaded {len(studies)} of {data.get('totalCount', '?')} trials")

        page_token = data.get("nextPageToken")
        if not page_token:
            return studies
        time.sleep(0.5)  # be polite to the API


def flatten(study):
    """Turn one nested API record into one flat row."""
    p = study["protocolSection"]
    ident = p.get("identificationModule", {})
    status = p.get("statusModule", {})
    design = p.get("designModule", {})
    locations = p.get("contactsLocationsModule", {}).get("locations", [])
    interventions = p.get("armsInterventionsModule", {}).get("interventions", [])

    # A trial can have hundreds of sites, so keep each country once.
    countries = sorted({loc["country"] for loc in locations if loc.get("country")})

    return {
        "nct_id": ident.get("nctId"),
        "title": ident.get("briefTitle"),
        "sponsor": p.get("sponsorCollaboratorsModule", {}).get("leadSponsor", {}).get("name"),
        "phase": " | ".join(design.get("phases", [])),
        "status": status.get("overallStatus"),
        "start_date": status.get("startDateStruct", {}).get("date"),
        "completion_date": status.get("completionDateStruct", {}).get("date"),
        "enrolment": design.get("enrollmentInfo", {}).get("count"),
        "enrolment_type": design.get("enrollmentInfo", {}).get("type"),
        "interventions": " | ".join(i["name"] for i in interventions if i.get("name")),
        "countries": " | ".join(countries),
    }


if __name__ == "__main__":
    studies = fetch_all_studies()
    df = pd.DataFrame([flatten(s) for s in studies])
    OUT_FILE.parent.mkdir(exist_ok=True)
    df.to_csv(OUT_FILE, index=False)
    Path("data/snapshot_date.txt").write_text(date.today().isoformat())  # shown on the dashboard
    print(f"\nSaved {len(df)} trials to {OUT_FILE}")
    print(df.head(3).to_string())
