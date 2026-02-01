from geopy.geocoders import Nominatim
from geopy.extra.rate_limiter import RateLimiter
from geopy.exc import GeocoderTimedOut, GeocoderUnavailable
from app.CONSTANTS import GEOCODER_USER_AGENT, GEOCODER_MIN_DELAY_SEC
import logging

_geolocator = Nominatim(user_agent=GEOCODER_USER_AGENT, timeout=10)
logger = logging.getLogger(__name__)

_forward = RateLimiter(
    _geolocator.geocode,
    min_delay_seconds=GEOCODER_MIN_DELAY_SEC,
    max_retries=2,
    error_wait_seconds=1.5,
    swallow_exceptions=False,
)

_reverse = RateLimiter(
    _geolocator.reverse,
    min_delay_seconds=GEOCODER_MIN_DELAY_SEC,
    max_retries=2,
    error_wait_seconds=1.5,
    swallow_exceptions=False,
)

def _normalize_address(address: str) -> str:
    a = (address or "").strip()
    if not a:
        return a

    lower = a.lower()
    if ("new york" not in lower) and ("ny" not in lower) and ("nyc" not in lower):
        a = f"{a}, New York, NY"
    return a

def geocode_forward(address: str):
    try:
        q = _normalize_address(address)
        loc = _forward(q)
        if not loc:
            logger.warning("geocode_forward no result address=%s", q)
            return None
        return {"lat": loc.latitude, "lon": loc.longitude, "display_name": loc.address}
    except (GeocoderTimedOut, GeocoderUnavailable):
        logger.exception("geocode_forward geocoder unavailable address=%s", address)
        return None
    except Exception:
        logger.exception("geocode_forward unexpected error address=%s", address)
        return None

def geocode_reverse(lat: float, lon: float):
    try:
        loc = _reverse((lat, lon), language="en")
        if not loc:
            logger.warning("geocode_reverse no result lat=%s lon=%s", lat, lon)
            return None
        return {"lat": lat, "lon": lon, "display_name": loc.address}
    except (GeocoderTimedOut, GeocoderUnavailable):
        logger.exception("geocode_reverse geocoder unavailable lat=%s lon=%s", lat, lon)
        return None
    except Exception:
        logger.exception("geocode_reverse unexpected error lat=%s lon=%s", lat, lon)
        return None
