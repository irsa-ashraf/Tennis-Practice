from fastapi import FastAPI, Query, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from starlette.responses import FileResponse
import pandas as pd
import logging

from app.settings import get_settings
from app.data_prep import load_or_build
from app.nearest import NearestIndex
from app.pydantic_models import Court, NearestResp
from app.geocode import geocode_forward, geocode_reverse
from app.pydantic_models import GeocodeReq, GeocodeResp, ReverseReq
from app.agent import router as agent_router
from app.CONSTANTS import TENNIS_CSV


def create_app():
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)

    settings = get_settings()
    app = FastAPI(title=settings.app_name)

    # Serve static files
    app.mount("/static", StaticFiles(directory="app/static"), name="static")

    # Serve the homepage
    @app.get("/", include_in_schema=False)
    def home():
        return FileResponse("app/static/index.html")

    # API routers
    app.include_router(agent_router)

    def _load_csv(path: str) -> pd.DataFrame:
        df = pd.read_csv(path)
        if "Lat" in df.columns:
            df["Lat"] = pd.to_numeric(df["Lat"], errors="coerce")
        if "Lon" in df.columns:
            df["Lon"] = pd.to_numeric(df["Lon"], errors="coerce")
        if "Num_Of_Courts" in df.columns:
            df["Num_Of_Courts"] = pd.to_numeric(df["Num_Of_Courts"], errors="coerce").fillna(0).astype(int)
        df = df.dropna(subset=["Lat", "Lon"]).reset_index(drop=True)
        return df

    def _normalize_sport(sport: str) -> str:
        s = (sport or "handball").strip().lower()
        if s in {"handball", "tennis"}:
            return s
        if s in {"both", "all"}:
            return "both"
        raise HTTPException(status_code=400, detail="Invalid sport. Use handball, tennis, or both.")

    # Load data + build indexes
    handball_df = load_or_build()
    if handball_df is None or handball_df.empty:
        raise RuntimeError("Failed to load handball courts dataset.")
    tennis_df = _load_csv(str(TENNIS_CSV))
    if tennis_df is None or tennis_df.empty:
        raise RuntimeError("Failed to load tennis courts dataset.")

    handball_idx = NearestIndex(handball_df)
    tennis_idx = NearestIndex(tennis_df)

    app.state.handball_df = handball_df
    app.state.tennis_df = tennis_df
    app.state.handball_idx = handball_idx
    app.state.tennis_idx = tennis_idx

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.allowed_origins,
        allow_credentials=settings.cors_allow_credentials,
        allow_methods=["*"],
        allow_headers=settings.cors_allow_headers,
    )

    @app.get("/health")
    def health():
        return {"status": "ok"}

    @app.post("/geocodeForward", response_model=GeocodeResp)
    def forward(req: GeocodeReq):
        logger.info("geocodeForward request address=%s", req.address)
        result = geocode_forward(req.address)
        if not result:
            logger.warning("geocodeForward failed address=%s", req.address)
            raise HTTPException(status_code=503, detail="Geocoding service unavailable")
        return GeocodeResp(**result)

    @app.post("/geocodeReverse", response_model=GeocodeResp)
    def reverse(req: ReverseReq):
        logger.info("geocodeReverse request lat=%s lon=%s", req.lat, req.lon)
        result = geocode_reverse(req.lat, req.lon)
        if not result:
            logger.warning("geocodeReverse failed lat=%s lon=%s", req.lat, req.lon)
            raise HTTPException(status_code=503, detail="Geocoding service unavailable")
        return GeocodeResp(**result)

    @app.get("/nearest", response_model=NearestResp)
    def nearest(
        lat: float = Query(..., ge=-90, le=90),
        lon: float = Query(..., ge=-180, le=180),
        limit: int = Query(10, ge=1, le=50),
        sport: str = Query("handball"),
    ):
        sport_norm = _normalize_sport(sport)

        def _rows_to_results(rows: pd.DataFrame, sport_name: str):
            results = []
            for _, r in rows.iterrows():
                results.append(
                    Court(
                        Court_Id=str(r.get("Court_Id")),
                        Name=str(r.get("Name")),
                        Borough=str(r.get("Borough", "")),
                        Lat=float(r.get("Lat")),
                        Lon=float(r.get("Lon")),
                        Num_Of_Courts=int(r.get("Num_Of_Courts")) if "Num_Of_Courts" in rows.columns else None,
                        Location=str(r.get("Location", "")),
                        Distance_Km=float(r.get("distance_km", 0.0)),
                        Sport=sport_name,
                    )
                )
            return results

        if sport_norm == "handball":
            nearest_df = app.state.handball_idx.query_k(lat, lon, k=limit)
            results = _rows_to_results(nearest_df, "handball")
            return NearestResp(count=len(results), results=results)

        if sport_norm == "tennis":
            nearest_df = app.state.tennis_idx.query_k(lat, lon, k=limit)
            results = _rows_to_results(nearest_df, "tennis")
            return NearestResp(count=len(results), results=results)

        handball_df = app.state.handball_idx.query_k(lat, lon, k=limit)
        tennis_df = app.state.tennis_idx.query_k(lat, lon, k=limit)
        merged = _rows_to_results(handball_df, "handball") + _rows_to_results(tennis_df, "tennis")
        merged = sorted(merged, key=lambda r: r.Distance_Km if r.Distance_Km is not None else 0.0)[:limit]

        return NearestResp(count=len(merged), results=merged)

    return app


app = create_app()
