from geopy.geocoders import Nominatim
from geopy.extra.rate_limiter import RateLimiter
from geopy.exc import GeocoderTimedOut, GeocoderUnavailable
from app.CONSTANTS import GEOCODER_USER_AGENT, GEOCODER_MIN_DELAY_SEC

_geolocator = Nominatim(user_agent=GEOCODER_USER_AGENT, timeout=10)

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
    # If user didn't specify NYC-ish context, add it.
    # This improves hit rate and reduces ambiguous matches.
    if ("new york" not in lower) and ("ny" not in lower) and ("nyc" not in lower):
        a = f"{a}, New York, NY"
    return a

def geocode_forward(address: str):
    try:
        q = _normalize_address(address)
        loc = _forward(q)
        if not loc:
            return None
        return {"lat": loc.latitude, "lon": loc.longitude, "display_name": loc.address}
    except (GeocoderTimedOut, GeocoderUnavailable):
        # temporary problems
        return None
    except Exception:
        # keep it safe: treat unknown errors as "no result"
        return None

def geocode_reverse(lat: float, lon: float):
    try:
        loc = _reverse((lat, lon), language="en")
        if not loc:
            return None
        return {"lat": lat, "lon": lon, "display_name": loc.address}
    except (GeocoderTimedOut, GeocoderUnavailable):
        return None
    except Exception:
        return None
