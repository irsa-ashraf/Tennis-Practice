'''
Contains rest endpoints
'''

from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from typing import Optional
import pandas as pd

from app.data_prep import load_or_build
from app.pydantic_models import GeocodeReq, GeocodeResp, ReverseReq, Court, NearestResp

app = FastAPI(title="NYC Tennis Courts", version="1.0.0")

# Load clean df at startup
df = load_or_build()


@app.get("/health_check")
def health_check():
    return {"status": "ok"}


@app.get("/", include_in_schema=False)
def root():
    return FileResponse("templates/index.html")


@app.get("/courts/{court_id}", response_model=Court)
def get_court(court_id: str):
    row = df[df["Court_Id"] == court_id]
    if row.empty:
        raise HTTPException(404, detail="Court not found")
    r = row.iloc[0]
    return Court(
        Court_Id=r["Court_Id"],
        Name=str(r["Name"]),
        Borough=str(r.get("Borough", "")),
        Lat=float(r["Lat"]),
        Lon=float(r["Lon"])
    )
