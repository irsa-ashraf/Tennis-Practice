'''
Clean raw data and prepare it for analysis.
'''


from __future__ import annotations
import pandas as pd
# from pathlib import Path
# from typing import Tuple
from .CONSTANTS import RAW_JSON, CLEAN_CSV


BOROUGH_PREFIXES = {
    "X": "Bronx",
    "B": "Brooklyn",
    "M": "Manhattan",
    "Q": "Queens",
    "R": "Staten Island",
}


def infer_borough(prop_id):
    '''
    Infer borough from Prop_ID prefix.
    Iputs:
        prop_id: str - Property ID, expected to start with a borough prefix.
    Returns:
        str - Borough name based on the prefix.
        If prefix is not recognized, returns empty string.
    Example:
        infer_borough("X12345") -> "Bronx"
    '''

    if not prop_id:
        return ""
    
    return BOROUGH_PREFIXES.get(prop_id.strip()[0:1].upper(), "")


def build_clean_csv(raw_json, out_csv):
    '''
    Build a clean CSV from raw JSON data.
    Inputs:
        raw_json: Path - Path to the raw JSON file.
        out_csv: Path - Path to save the cleaned CSV.
    Returns:
        pd.DataFrame - Cleaned DataFrame with columns: court_id, name, borough, lat, lon.
    Raises:
        FileNotFoundError - If the raw JSON file does not exist.
        ValueError - If expected columns are missing in the raw JSON.   
    '''

    if not raw_json.exists():
        raise FileNotFoundError(f"Raw JSON not found at {raw_json}")

    df = pd.read_json(raw_json)

    # Normalize columns
    df.columns = [c.strip().lower() for c in df.columns]

    # Ensure numeric lat/lon
    for col in ["lat", "lon"]:
        if col not in df.columns:
            raise ValueError("Expected 'lat' and 'lon' columns in the raw JSON.")
        df[col] = pd.to_numeric(df[col], errors="coerce")

    # Drop rows without coordinates
    df = df.dropna(subset=["lat", "lon"]).copy()

    #  Extract borough from Prop_ID
    if "borough" not in df.columns:
        df["borough"] = df.get("prop_id", "").apply(infer_borough)

    # # add primary key if missing
    # if "court_id" not in df.columns:
    #     df = df.reset_index(drop=False).rename(columns={"index": "court_id"})

    # Clean schema
    clean = df[["prop_id", "name", "borough", "location", "Num_of_Courts", "lat", "lon"]].copy()
    clean = clean.rename(columns={"prop_id": "court_id"})
    clean.columns = [col.title() for col in clean.columns]

    # Save to csv
    clean.to_csv(out_csv, index=False)

    return clean


def load_or_build():
    '''
    Load cleaned CSV if it exists, otherwise build it from raw JSON
    Returns:
        pd.DataFrame - Cleaned DataFrame with columns: court_id, name, borough, lat, lon.
    Raises:
        FileNotFoundError - If the raw JSON file does not exist.
        ValueError - If expected columns are missing in the raw JSON..
    '''

    if CLEAN_CSV.exists():
        return pd.read_csv(CLEAN_CSV)
    
    return build_clean_csv(RAW_JSON, CLEAN_CSV)


# Run script
if __name__ == "__main__":
    try:
        df = load_or_build()
        print(f"Cleaned data loaded with {len(df)} records.")
    except Exception as e:
        print(f"Error: {e}")    