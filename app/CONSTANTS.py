'''
Root directory paths and constants
'''

from pathlib import Path

# Paths
ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"
RAW_JSON = DATA_DIR / "DPR_Handball_001.json"
CLEAN_CSV = DATA_DIR / "handball_courts_clean.csv"

# Geo
EARTH_RADIUS_KM = 6371.0088

# Geocoding
GEOCODER_USER_AGENT = "tennis-practice"
GEOCODER_MIN_DELAY_SEC = 1.0