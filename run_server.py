# run_server.py
"""
Helper script to run the FastAPI app locally.

Usage:
    python run_server.py
"""

import uvicorn
from app.settings import get_settings


def main():
    """
    Launch the FastAPI app with uvicorn, using settings from environment variables.
    """
    settings = get_settings()
    uvicorn.run(
        "app.server:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
    )


if __name__ == "__main__":
    main()
