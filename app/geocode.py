from geopy.geocoders import Nominatim
from geopy.extra.rate_limiter import RateLimiter
from app.CONSTANTS import GEOCODER_USER_AGENT, GEOCODER_MIN_DELAY_SEC

_geolocator = Nominatim(user_agent=GEOCODER_USER_AGENT)
_forward = RateLimiter(_geolocator.geocode, min_delay_seconds=GEOCODER_MIN_DELAY_SEC)
_reverse = RateLimiter(_geolocator.reverse, min_delay_seconds=GEOCODER_MIN_DELAY_SEC)

def forward(address: str):
    loc = _forward(address)
    if not loc:
        return None
    return {"lat": loc.latitude, "lon": loc.longitude, "display_name": loc.address}

def reverse(lat: float, lon: float):
    loc = _reverse((lat, lon), language="en")
    if not loc:
        return None
    return {"lat": lat, "lon": lon, "display_name": loc.address}
