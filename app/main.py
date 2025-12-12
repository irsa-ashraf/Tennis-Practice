'''
FastAPI app: serves the UI and provides /nearest, /geocode, /reverse_geocode, /courts/{id}
'''

from __future__ import annotations
from typing import Optional, List

import os
import pandas as pd
from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import FileResponse
from app.agent import router as agent_router

# ---- Imports (works whether running as a package "app.*" or flat files) ----
try:
    from app.data_prep import load_or_build
except ImportError:  # fallback if not running as a package
    from data_prep import load_or_build

try:
    from app.pydantic_models import GeocodeReq, GeocodeResp, ReverseReq, Court, NearestResp
except ImportError:
    from pydantic_models import GeocodeReq, GeocodeResp, ReverseReq, Court, NearestResp

try:
    from app.nearest import NearestIndex
except ImportError:
    from app.nearest import NearestIndex

try:
    from app.geocode import forward as geocode_forward, reverse as geocode_reverse
except ImportError:
    from app.geocode import forward as geocode_forward, reverse as geocode_reverse


app = FastAPI(title="NYC Tennis Courts", version="1.0.0")
app.include_router(agent_router)

# ---- Load data and build nearest index ----
# CSV has Title-Case columns (Court_Id, Name, Borough, Lat, Lon, …).
df: pd.DataFrame = load_or_build()

# Build an index on a LOWER-CASED copy so NearestIndex (which expects 'lat','lon') works.
_df_for_index = df.rename(columns={c: c.lower() for c in df.columns})
idx = NearestIndex(_df_for_index)


# ---- Helpers ----
def _index_html_path() -> str:
    """
    Try to serve ./index.html (repo root). If not found, fall back to ./templates/index.html.
    """
    candidate1 = os.path.join(os.getcwd(), "index.html")
    if os.path.exists(candidate1):
        return candidate1
    candidate2 = os.path.join(os.getcwd(), "templates", "index.html")
    if os.path.exists(candidate2):
        return candidate2
    # Final fallback: 404 via FileResponse will raise, but we can at least point to expected file.
    return candidate1


# ---- Endpoints ----
@app.get("/health_check")
def health_check():
    return {"status": "ok"}


@app.get("/", include_in_schema=False)
def root():
    # Serve uploaded index.html. Keep it in repo root next to run_server.py.
    return FileResponse(_index_html_path())


@app.get("/courts/{court_id}", response_model=Court)
def get_court(court_id: str):
    # DataFrame columns are Title-Case (Court_Id, Name, Borough, Lat, Lon, …)
    row = df[df["Court_Id"] == court_id]
    if row.empty:
        raise HTTPException(404, detail="Court not found")
    r = row.iloc[0]
    return Court(
        Court_Id=str(r["Court_Id"]),
        Name=str(r["Name"]),
        Borough=str(r.get("Borough", "")),
        Lat=float(r["Lat"]),
        Lon=float(r["Lon"]),
        Distance_Km=None,  # not applicable here
    )


@app.get("/nearest", response_model=NearestResp)
def nearest(
    lat: float = Query(..., ge=-90, le=90),
    lon: float = Query(..., ge=-180, le=180),
    limit: int = Query(10, ge=1, le=50),
):
    """
    Return the K nearest courts to (lat, lon) using the prebuilt BallTree index.

    Notes:
        - The index lives on app.state.idx (loaded at startup).
        - Returned rows have lower-case columns; we map to your Pydantic model's
          Title-Case fields.
    Inputs:
        lat: (float) latitude in degrees
        lon: (float) longitude in degrees
        limit: (int) number of results to return (1–50)

    Returns:
        (NearestResp) count and list of Court objects with distance_km
    """
    rows = app.state.idx.query_k(lat, lon, k=limit)

    results: List[Court] = []
    for r in rows.itertuples(index=False):
        results.append(
            Court(
                Court_Id=str(getattr(r, "court_id")),
                Name=str(getattr(r, "name")),
                Borough=str(getattr(r, "borough", "") or ""),
                Lat=float(getattr(r, "lat")),
                Lon=float(getattr(r, "lon")),
                Distance_Km=float(getattr(r, "distance_km")),
            )
        )

    return NearestResp(count=len(results), results=results)


@app.post("/geocode", response_model=GeocodeResp)
def geocode(req: GeocodeReq):
    """
    Forward geocoding: address -> (lat, lon, display_name)
    """
    hit = geocode_forward(req.address)
    if not hit:
        raise HTTPException(status_code=404, detail="Address not found")
    return GeocodeResp(**hit)


@app.post("/reverse_geocode", response_model=GeocodeResp)
def reverse_geocode(req: ReverseReq):
    """
    Reverse geocoding: (lat, lon) -> display_name
    """
    hit = geocode_reverse(req.lat, req.lon)
    if not hit:
        raise HTTPException(status_code=404, detail="Location not found")
    return GeocodeResp(**hit)
