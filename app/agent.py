import os
import json
import logging
from functools import lru_cache
from typing import Any, Dict, List, Optional

import pandas as pd
from fastapi import APIRouter, HTTPException
from openai import OpenAI

from app.CONSTANTS import CLEAN_CSV
from app.nearest import NearestIndex
from app.pydantic_models import AgentRequest
from app.geocode import geocode_forward

router = APIRouter()
logger = logging.getLogger(__name__)

def _get_client() -> OpenAI:
    api_key = os.getenv("NYCPLACES_OPENAI_API_KEY")
    if not api_key:
        raise HTTPException(status_code=500, detail="Missing NYCPLACES_OPENAI_API_KEY")
    return OpenAI(api_key=api_key)


@lru_cache(maxsize=1)
def _load_df() -> pd.DataFrame:
    if not CLEAN_CSV.exists():
        raise RuntimeError(f"CSV not found at: {CLEAN_CSV}")
    df = pd.read_csv(CLEAN_CSV)

    if "Lat" in df.columns:
        df["Lat"] = pd.to_numeric(df["Lat"], errors="coerce")
    if "Lon" in df.columns:
        df["Lon"] = pd.to_numeric(df["Lon"], errors="coerce")
    if "Num_Of_Courts" in df.columns:
        df["Num_Of_Courts"] = pd.to_numeric(df["Num_Of_Courts"], errors="coerce").fillna(0).astype(int)

    df = df.dropna(subset=["Lat", "Lon"]).reset_index(drop=True)
    return df


@lru_cache(maxsize=1)
def _nearest_index() -> NearestIndex:
    return NearestIndex(_load_df())

# Tools (CSV-backed)
def tool_dataset_summary() -> Dict[str, Any]:
    df = _load_df()
    locations = int(len(df))
    total_courts = int(df["Num_Of_Courts"].sum()) if "Num_Of_Courts" in df.columns else locations
    boroughs = sorted([b for b in df["Borough"].dropna().unique()]) if "Borough" in df.columns else []
    return {
        "locations": locations,
        "total_courts": total_courts,
        "boroughs": boroughs,
        "columns": list(df.columns),
    }


def tool_courts_by_borough(borough: str) -> Dict[str, Any]:
    df = _load_df()
    if "Borough" not in df.columns:
        return {"error": "CSV does not contain Borough column."}

    b = (borough or "").strip().lower()
    if not b:
        return {"error": "borough is required"}

    # Normalize common abbreviations
    aliases = {
        "bk": "brooklyn",
        "bx": "bronx",
        "mn": "manhattan",
        "si": "staten island",
        "queens": "queens",
        "brooklyn": "brooklyn",
        "bronx": "bronx",
        "manhattan": "manhattan",
        "staten island": "staten island",
    }
    b = aliases.get(b, b)

    sub = df[df["Borough"].astype(str).str.lower() == b]
    locations = int(len(sub))
    total_courts = int(sub["Num_Of_Courts"].sum()) if "Num_Of_Courts" in sub.columns else locations
    return {"borough": borough, "locations": locations, "total_courts": total_courts}


def tool_search_courts(name_contains: str, limit: int = 10) -> Dict[str, Any]:
    df = _load_df()
    if "Name" not in df.columns:
        return {"error": "CSV does not contain Name column."}

    q = (name_contains or "").strip().lower()
    if not q:
        return {"error": "name_contains is required"}

    sub = df[df["Name"].astype(str).str.lower().str.contains(q, na=False)].head(max(1, min(int(limit), 25)))
    results = []
    for _, r in sub.iterrows():
        results.append({
            "Name": r.get("Name"),
            "Borough": r.get("Borough"),
            "Num_Of_Courts": int(r.get("Num_Of_Courts")) if "Num_Of_Courts" in df.columns else None,
            "Lat": float(r.get("Lat")),
            "Lon": float(r.get("Lon")),
        })
    return {"query": name_contains, "count": len(results), "results": results}


def tool_nearest_courts(lat: float, lon: float, limit: int = 5) -> Dict[str, Any]:
    idx = _nearest_index()
    k = max(1, min(int(limit), 10))
    rows = idx.query_k(lat=float(lat), lon=float(lon), k=k)
    out = []
    for _, r in rows.iterrows():
        out.append({
            "Name": r.get("Name"),
            "Borough": r.get("Borough"),
            "Num_Of_Courts": int(r.get("Num_Of_Courts")) if "Num_Of_Courts" in rows.columns else None,
            "Lat": float(r.get("Lat")),
            "Lon": float(r.get("Lon")),
            "distance_km": float(r.get("distance_km", 0.0)),
        })
    return {"lat": lat, "lon": lon, "count": len(out), "results": out}


def tool_nearest_to_address(address: str, limit: int = 5) -> Dict[str, Any]:
    geo = geocode_forward(address)
    if not geo:
        return {
            "error": "Address not found",
            "hint": "Try adding a borough, ZIP code, or 'NYC'. Example: '399 Park Ave, Manhattan, NY'.",
        }
    return {
        "address": address,
        "display_name": geo.get("display_name"),
        **tool_nearest_courts(lat=geo["lat"], lon=geo["lon"], limit=limit),
    }


TOOLS = [
    {
        "type": "function",
        "name": "dataset_summary",
        "description": "Get high-level summary of the handball courts dataset (counts, boroughs, columns).",
        "parameters": {"type": "object", "properties": {}, "required": []},
    },
    {
        "type": "function",
        "name": "courts_by_borough",
        "description": "Get number of locations and total courts in a given borough (e.g., Manhattan, Brooklyn, Queens, Bronx, Staten Island).",
        "parameters": {
            "type": "object",
            "properties": {
                "borough": {"type": "string"},
            },
            "required": ["borough"],
        },
    },
    {
        "type": "function",
        "name": "search_courts",
        "description": "Search court locations by name substring.",
        "parameters": {
            "type": "object",
            "properties": {
                "name_contains": {"type": "string"},
                "limit": {"type": "integer", "minimum": 1, "maximum": 25},
            },
            "required": ["name_contains"],
        },
    },
    {
        "type": "function",
        "name": "nearest_courts",
        "description": "Find nearest courts to a latitude/longitude.",
        "parameters": {
            "type": "object",
            "properties": {
                "lat": {"type": "number"},
                "lon": {"type": "number"},
                "limit": {"type": "integer", "minimum": 1, "maximum": 10},
            },
            "required": ["lat", "lon"],
        },
    },
    {
        "type": "function",
        "name": "nearest_to_address",
        "description": "Geocode an address then find nearest courts to that address.",
        "parameters": {
            "type": "object",
            "properties": {
                "address": {"type": "string"},
                "limit": {"type": "integer", "minimum": 1, "maximum": 10},
            },
            "required": ["address"],
        },
    },
]


def _run_tool(name: str, args: Dict[str, Any]) -> Dict[str, Any]:
    if name == "dataset_summary":
        return tool_dataset_summary()
    if name == "courts_by_borough":
        return tool_courts_by_borough(**args)
    if name == "search_courts":
        return tool_search_courts(**args)
    if name == "nearest_courts":
        return tool_nearest_courts(**args)
    if name == "nearest_to_address":
        return tool_nearest_to_address(**args)
    return {"error": f"Unknown tool: {name}"}


@router.get("/agent_health")
def agent_health():
    _ = _load_df()
    return {"status": "ok"}


@router.post("/agent")
async def agent(request: AgentRequest):
    query = (request.query or "").strip()
    if not query:
        raise HTTPException(status_code=400, detail="Query cannot be empty")

    client = _get_client()

    input_list: List[Dict[str, Any]] = [
        {
            "role": "system",
            "content": (
                "You are an assistant for a NYC Handball Courts web app. "
                "Answer using the dataset tools when relevant. "
                "Be concise, correct, and include numbers when asked. "
                "If the user's request is ambiguous, ask a brief follow-up question. "
                "If the user asks something unrelated to the dataset, say you can only answer court/dataset questions and suggest a relevant example."
            ),
        },
        {"role": "user", "content": query},
    ]

    # Ask model
    try:
        resp = client.responses.create(
            model="gpt-5-mini",
            tools=TOOLS,
            input=input_list,
        )
    except Exception as e:
        logger.exception("agent: initial model call failed")
        raise HTTPException(status_code=503, detail="Assistant is temporarily unavailable. Please try again.") from e

    # Add model output to the running input list
    input_list += resp.output

    # Execute any tool calls
    for item in resp.output:
        if getattr(item, "type", None) == "function_call":
            args = json.loads(item.arguments or "{}")
            result = _run_tool(item.name, args)
            if isinstance(result, dict) and result.get("error"):
                logger.info("agent tool error name=%s error=%s", item.name, result.get("error"))

            input_list.append(
                {
                    "type": "function_call_output",
                    "call_id": item.call_id,
                    "output": json.dumps(result),
                }
            )

    # Ask model again to produce final user-facing answer
    try:
        final = client.responses.create(
            model="gpt-5-mini",
            tools=TOOLS,
            input=input_list,
            instructions="Answer the user clearly and concisely. Use the tool results. Do not mention tool call IDs.",
        )
    except Exception as e:
        logger.exception("agent: final model call failed")
        raise HTTPException(status_code=503, detail="Assistant is temporarily unavailable. Please try again.") from e

    return {"text": final.output_text}
