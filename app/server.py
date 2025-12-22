from fastapi import FastAPI, Query, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from starlette.responses import FileResponse
import pandas as pd

from app.settings import get_settings
from app.data_prep import load_or_build
from app.nearest import NearestIndex
from app.pydantic_models import Court, NearestResp
from app.geocode import geocode_forward, geocode_reverse
from app.pydantic_models import GeocodeReq, GeocodeResp, ReverseReq
from app.agent import router as agent_router


def create_app():
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

    # Load data + build index
    df = load_or_build()
    if df is None or df.empty:
        raise RuntimeError("Failed to load handball courts dataset.")
    idx = NearestIndex(df)
    app.state.df = df
    app.state.idx = idx

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
        result = geocode_forward(req.address)
        if not result:
            raise HTTPException(status_code=503, detail="Geocoding service unavailable")
        return GeocodeResp(**result)

    @app.post("/geocodeReverse", response_model=GeocodeResp)
    def reverse(req: ReverseReq):
        result = geocode_reverse(req.lat, req.lon)
        if not result:
            raise HTTPException(status_code=503, detail="Geocoding service unavailable")
        return GeocodeResp(**result)

    @app.get("/nearest", response_model=NearestResp)
    def nearest(
        lat: float = Query(..., ge=-90, le=90),
        lon: float = Query(..., ge=-180, le=180),
        limit: int = Query(10, ge=1, le=50),
    ):
        nearest_df = idx.query_k(lat, lon, k=limit)

        if "Court_Id" not in nearest_df.columns:
            nearest_df = nearest_df.reset_index().rename(columns={"index": "Court_Id"})

        results = []
        for _, r in nearest_df.iterrows():
            results.append(
                Court(
                    Court_Id=str(r["Court_Id"]),
                    Name=str(r["Name"]),
                    Borough=str(r.get("Borough", "")),
                    Lat=float(r["Lat"]),
                    Lon=float(r["Lon"]),
                    Num_Of_Courts=int(r["Num_Of_Courts"]),
                    Location=str(r["Location"]),
                    Distance_Km=float(r.get("distance_km", 0.0)),
                )
            )

        return NearestResp(count=len(results), results=results)

    return app


app = create_app()
