# app/server.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from starlette.responses import FileResponse, RedirectResponse

from .settings import get_settings


def create_app():
    """
    Create and configure the FastAPI application.

    Returns:
        (FastAPI) configured FastAPI app instance
    """
    settings = get_settings()

    app = FastAPI(title=settings.app_name)

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
