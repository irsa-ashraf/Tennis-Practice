# app/server.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from starlette.responses import FileResponse, RedirectResponse
from app.settings import get_settings
import pandas as pd
from fastapi import Query, HTTPException
from app.data_prep import load_or_build
from app.nearest import NearestIndex
from app.pydantic_models import Court, NearestResp
from typing import List
from app.geocode import forward as geocode_forward, reverse as geocode_reverse
from app.pydantic_models import GeocodeReq, GeocodeResp, ReverseReq



def load_data(data_dir):
    """
    Load or build the cleaned courts dataset.

    Inputs:
        data_dir: (pathlib.Path) directory where raw/clean data files live

    Returns:
        (pd.DataFrame) cleaned courts dataframe with columns:
            court_id, name, borough, lat, lon, ...
    """
    df = load_or_build(base_dir=str(data_dir))
    if df is None or df.empty:
        raise RuntimeError("Failed to load handball courts dataset.")
    return df


def build_index(df):
    """
    Build the nearest-neighbor index for courts.

    Inputs:
        df: (pd.DataFrame) courts dataframe with lat/lon

    Returns:
        (NearestIndex) spatial index for fast KNN queries
    """
    return NearestIndex(df)


def create_app():
    """
    Create and configure the FastAPI application.

    Returns:
        (FastAPI) configured FastAPI app instance
    """
    settings = get_settings()

    app = FastAPI(title=settings.app_name)

    # Load data + index at startup
    df: pd.DataFrame = load_data(settings.data_dir)
    idx: NearestIndex = build_index(df)


    @app.on_event("startup")
    def startup_event():
        """
        Log dataset and index status when the app starts.
        """
        court_count = len(app.state.df)
        print(f"[Startup] Loaded {court_count} courts into memory.")
        print(f"[Startup] NearestIndex is ready for queries.")


    # stash on app.state for reuse in endpoints
    app.state.df = df
    app.state.idx = idx

    # CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.allowed_origins,
        allow_credentials=settings.cors_allow_credentials,
        allow_methods=["*"],
        allow_headers=settings.cors_allow_headers,
    )

    # Static files (serves /static/*)
    app.mount(
        "/static",
        StaticFiles(directory=str(settings.static_dir), html=True),
        name="static",
    )

    @app.get("/health")
    def health():
        """
        Health and readiness probe.

        Returns:
            (dict) service status and metadata
        """
        return {"status": "ok", "app": settings.app_name, "debug": settings.debug}

    @app.get("/")
    def root():
        """
        Serve the main index page or redirect to /static if not found.

        Returns:
            (FileResponse or RedirectResponse) index.html or redirect
        """
        index_path = settings.static_dir / "index.html"
        if index_path.exists():
            return FileResponse(str(index_path))
        return RedirectResponse(url="/static")


    @app.post("/geocode", response_model=GeocodeResp)
    def geocode(req: GeocodeReq):
        """
        Convert a free-form address into latitude/longitude.

        Inputs:
            req: (GeocodeReq) Pydantic model with field:
                - address: (str) address or place

        Returns:
            (GeocodeResp) latitude, longitude, and display name
        """
        result = geocode_forward(req.address)
        if not result:
            raise HTTPException(status_code=404, detail="Address not found")
        return GeocodeResp(**result)

    
    @app.post("/reverse", response_model=GeocodeResp)
    def reverse(req: ReverseReq):
        """
        Convert latitude/longitude into a human-readable address.

        Inputs:
            req: (ReverseReq) Pydantic model with fields:
                - lat: (float) latitude
                - lon: (float) longitude

        Returns:
            (GeocodeResp) latitude, longitude, and display name
        """
        result = geocode_reverse(req.lat, req.lon)
        if not result:
            raise HTTPException(status_code=404, detail="Coordinates not found")
        return GeocodeResp(**result)

    
    return app


# ASGI entrypoint
app = create_app()


if __name__ == "__main__":
    """
    Run the server directly with: python -m app.server
    Uses HOST/PORT/DEBUG from environment variables.
    """
    import uvicorn

    settings = get_settings()
    uvicorn.run(
        "app.server:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
    )
