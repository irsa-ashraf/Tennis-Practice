# NYC Tennis Court Finder (Web)

FastAPI + Leaflet app that ingests raw NYC Parks court data (`DPR_Handball_001.json`), cleans it, builds a spatial index (BallTree + haversine), and shows the **nearest** courts to the user's location or a typed address.

## Quickstart

Python = 3.11

http://127.0.0.1:8000/

1) **Python**
```bash
python -m venv .venv && source .venv/bin/activate    # Windows: .venv\Scripts\activate
pip install -r requirements.txt

