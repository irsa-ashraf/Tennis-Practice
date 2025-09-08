# app/settings.py
from __future__ import annotations

import os
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import List


def env_bool(key, default = False):
    """
    Parse boolean-like env vars: 1/0, true/false, yes/no
    Inputs: 
        key: (str) environment variable key
        default: (bool) default value if env var is not set
    Returns: 
        (bool) parsed boolean value
    """

    val = os.getenv(key)
    if val is None:
        return default
    
    return val.strip().lower() in {"1", "true", "yes", "y", "on"}


def env_list(key, default=None):
    """
    Parse a comma-separated environment variable into a list of strings.

    Inputs:
        key: (str) environment variable key
        default: (list or None) default list if env var is not set

    Returns:
        (list) list of parsed string values
    """
    val = os.getenv(key)
    if not val:
        return list(default or [])
    return [x.strip() for x in val.split(",") if x.strip()]


def env_int(key, default):
    """
    Parse an environment variable into an integer.

    Inputs:
        key: (str) environment variable key
        default: (int) default integer value if env var is not set

    Returns:
        (int) parsed integer value
    """
    val = os.getenv(key)
    if val is None:
        return default
    try:
        return int(val)
    except ValueError:
        return default


@dataclass(frozen=True)
class Settings:
    """
    Runtime configuration for the NYC Handball Finder service.

    All values can be overridden via environment variables so the app can run
    unchanged on any server, container, or host.
    """
    app_name: str
    host: str
    port: int
    debug: bool
    static_dir: Path
    data_dir: Path
    allowed_origins: List[str]
    cors_allow_credentials: bool
    cors_allow_headers: List[str]

    def is_prod(self):
        """
        Check if the application is running in production mode.

        Returns:
            (bool) True if debug mode is off, otherwise False
        """
        return not self.debug


@lru_cache(maxsize=1)
def get_settings():
    """
    Load and cache application settings from environment variables.

    Returns:
        (Settings) a settings dataclass instance with all config values
    """
    root = Path(__file__).resolve().parents[1]

    return Settings(
        app_name=os.getenv("APP_NAME", "NYC Handball Finder"),
        host=os.getenv("HOST", "0.0.0.0"),
        port=env_int("PORT", 8000),
        debug=env_bool("DEBUG", True),
        static_dir=Path(os.getenv("STATIC_DIR", str(root / "static"))),
        data_dir=Path(os.getenv("DATA_DIR", str(root / "data"))),
        allowed_origins=env_list("ALLOWED_ORIGINS", ["*"]),
        cors_allow_credentials=env_bool("CORS_ALLOW_CREDENTIALS", False),
        cors_allow_headers=env_list("CORS_ALLOW_HEADERS", ["*"]),
    )